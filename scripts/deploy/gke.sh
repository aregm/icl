#!/usr/bin/env bash

# Deploys ICL cluster to GCP

set -e

# Default values that can be overriden by corresponding environment variables
: ${X1_CLUSTER_NAME:="icl-$USER"}
: ${X1_GCP_ZONE:="us-central1-a"}
: ${ICL_INGRESS_DOMAIN:="test.x1infra.com"}
: ${X1_CLUSTER_VERSION:="1.28"}
: ${X1_EXTERNALDNS_ENABLED:="false"}
: ${CONTROL_NODE_IMAGE:="pbchekin/ccn-gcp:0.0.2"}
: ${ICL_GCP_MACHINE_TYPE:="e2-standard-4"}
: ${GKE_GPU_DRIVER_VERSION:="DEFAULT"}
: ${GPU_MODEL:=""}
: ${CREATE_BASTION:="false"}
: ${BASTION_SOURCE_RANGES:=""}

# GLOBAL VARIABLES
declare -g GPU_TYPE
declare -g GPU_ENABLED
declare -g JUPYTERHUB_EXTRA_RESOURCE_LIMITS

#: ${X1_GCP_REGION:="us-central1"}
# disabled since we use monozone cluster

# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$SCRIPT_DIR/functions.sh"
# workspace is relative to PROJECT_ROOT
WORKSPACE="workspace/$X1_CLUSTER_NAME"

function show_help() {
  cat <<EOF
Usage: $(basename $0) [option]

Options:
  --help              Show this help
  --console           Start control node console
  --check             Run a quick check for Docker and network connectivity
  --render            Create workspace directory
  --deploy-gke        Deploy GKE cluster only
  --deploy-x1         Deploy X1 workloads only
  --config            Generate Kubernetes config
  --delete            Delete workloads, cluster and workspace
  --delete-x1         Delete X1 workloads only
  --delete-gke        Delete GKE cluster only
  --gcloud-login      Login to gcloud via "gcloud auth login" and
                      store configuration to local ~/.config/gcloud
  --start-proxy       Start a proxy container
  --stop-proxy        Stop a proxy container

Environment variables:
  X1_CLUSTER_NAME                Cluster name, must be unique in the region, default is icl-$USER
  X1_GCP_PROJECT_NAME            GCP project name
  X1_GCP_ZONE                    GCP zone to use, default is us-central1-a
  ICL_INGRESS_DOMAIN             Domain for ingress, default is test.x1infra.com
  GOOGLE_APPLICATION_CREDENTIALS Location of a Google Cloud credential JSON file.
  ICL_GCP_MACHINE_TYPE           Machine type for GKE to use
  GPU_MODEL                      GPU being requested from GCP (e.g. nvidia-tesla-t4)
  TF_PG_CONN_STR                 If set, PostgreSQL backend will be used to store Terraform state 
  PGUSER                         PostgreSQL username for Terraform state
  PGPASSWORD                     PostgreSQL password for Terraform state
  GKE_GPU_DRIVER_VERSION         NVIDIA driver setting for GKE. Accepts "DEFAULT" or "LATEST".
  CREATE_BASTION                 Boolean value which controls the creation of bastion host if required by environment
  BASTION_SOURCE_RANGES          Comma separated list of CIDR addresses to allow SSH from e.g. "1.1.1.1/1","2.2.2.2/2"
EOF
}

function show_parameters() {
  for var in X1_GCP_ZONE ICL_INGRESS_DOMAIN WORKSPACE; do
    echo "$var: ${!var}"
  done
}

# Function to check if SOURCE_RANGES is empty
check_source_ranges() {
  if [ -z "${BASTION_SOURCE_RANGES}" ] || [ "${BASTION_SOURCE_RANGES}" == '""' ]; then
    echo "Error: BASTION_SOURCE_RANGES must be set and cannot be empty when CREATE_BASTION=\"true\""
    exit 1
  fi
}

# TODO: add cluster_version here
function render_gcp_terraform_tfvars() {
  if [[ -v TERRAFORM_POSTGRESQL_URI  ]]; then
    cat <<EOF > "$WORKSPACE/terraform/gcp/terraform.tfvars"
    terraform {
      backend "pg" {}
    }
EOF
  fi

  # Check and convert the string to a JSON array format if CREATE_BASTION is true
  if [[ "${CREATE_BASTION}" == "true" ]]; then
    check_source_ranges
    bastion_source_ranges_list=$(echo $BASTION_SOURCE_RANGES | sed 's/,/","/g' | sed 's/^/["/' | sed 's/$/"]/')
    generate_bastion_key
  fi

  cat <<EOF >> "$WORKSPACE/terraform/gcp/terraform.tfvars"
cluster_name = "$X1_CLUSTER_NAME"
gcp_zone = "$X1_GCP_ZONE"
gcp_project = "$X1_GCP_PROJECT_NAME"
node_version = "$X1_CLUSTER_VERSION"
machine_type = "$ICL_GCP_MACHINE_TYPE"
gke_gpu_driver_version = "$GKE_GPU_DRIVER_VERSION"
gpu_enabled="$GPU_ENABLED"
gpu_model = "$GPU_MODEL"
create_bastion = "$CREATE_BASTION"
bastion_public_key_content = "$bastion_public_key_content"
bastion_username = "$USER"
bastion_source_ranges = $bastion_source_ranges_list
EOF
}

function generate_bastion_key {
  # Create ~/.ssh directory if it doesn't exist and set permissions to 0700
  if [ ! -d "$HOME/.ssh" ]; then
    mkdir "$HOME/.ssh"
    chmod 0700 "$HOME/.ssh"
  fi
  # Generate an SSH key with an empty passphrase
  if [ ! -f "$HOME/.ssh/rsa_gcp.pub" ]; then
    ssh-keygen -t rsa -f "$HOME/.ssh/rsa_gcp" -C "$USER" -N ""
  fi
  # Set the value of $bastion_public_key_content to the contents of rsa_gcp.pub file
  bastion_public_key_content=$(cat "$HOME/.ssh/rsa_gcp.pub")
  # Export the variable to make it available in the current session
  export bastion_public_key_content
}

# Queries for the specific GPU included in the provided ICL_GCP_MACHINE_TYPE and X1_GCP_ZONE
function set_gpu_type() {
    # Check if GPU_MODEL contains the substrings [amd, intel, nvidia] and assign variables
    if [[ $GPU_MODEL == *"nvidia"* ]]; then
        GPU_ENABLED=true
        GPU_TYPE="nvidia"
        JUPYTERHUB_EXTRA_RESOURCE_LIMITS='nvidia.com/gpu'
    elif [[ $GPU_MODEL == *"intel"* ]]; then
        GPU_ENABLED=true
        GPU_TYPE="intel"
        JUPYTERHUB_EXTRA_RESOURCE_LIMITS='gpu.intel.com/i915'
    elif [[ $GPU_MODEL == *"amd"* ]]; then
        GPU_ENABLED=true
        GPU_TYPE="amd"
        JUPYTERHUB_EXTRA_RESOURCE_LIMITS='amd.com/gpu'
    else
        GPU_ENABLED=false
        GPU_TYPE="none"
        JUPYTERHUB_EXTRA_RESOURCE_LIMITS=''
    fi
}

function x1_terraform_args() {
  terraform_extra_args=(
    -var prometheus_enabled=false
    -var ingress_domain="${ICL_INGRESS_DOMAIN}"
    -var ingress_nginx_service_enabled=true
    -var local_path_enabled=false # use standard-rwo for GKE instead
    -var default_storage_class="standard-rwo"
    -var ray_load_balancer_enabled=false
    -var externaldns_enabled="${X1_EXTERNALDNS_ENABLED}"
    -var gpu_enabled="${GPU_ENABLED}"
    -var gpu_type="${GPU_TYPE}"
    -var jupyterhub_extra_resource_limits="${JUPYTERHUB_EXTRA_RESOURCE_LIMITS}"
    -var use_node_ip_for_user_ports=true
    -var use_external_node_ip_for_user_ports=true
  )
  if [[ -v X1_TERRAFORM_DISABLE_LOCKING || -v ICL_TERRAFORM_DISABLE_LOCKING ]]; then
    terraform_extra_args+=( -lock=false )
  fi
  # TODO: add lock release here
  echo "${terraform_extra_args[*]}"
}

function check_gcp_auth()
{
  control_node "gcloud container clusters list" 2>/dev/null || gcloud_login
}

# Deploy cluster
function deploy_gke() {
  check_gcp_auth
  control_node "terraform -chdir=$WORKSPACE/terraform/gcp/ apply -input=false -auto-approve"
}

# Delete cluster
function delete_gke() {
  check_gcp_auth
  control_node "terraform -chdir=$WORKSPACE/terraform/gcp/ destroy -input=false -auto-approve"
}

function update_config() {
  control_node "gcloud container clusters get-credentials $X1_CLUSTER_NAME --zone=$X1_GCP_ZONE"
}

# Create workspace
function render_workspace() {
  control_node "\
    mkdir -p /work/x1/$WORKSPACE/terraform/gcp \
    && cp -r /work/x1/terraform/gcp/* /work/x1/$WORKSPACE/terraform/gcp/
  "
  control_node "test -f /work/x1/$WORKSPACE/terraform/gcp/terraform.tfvars" ||\
  render_gcp_terraform_tfvars
  if [[ -v TF_PG_CONN_STR  ]]; then
    cat <<EOF > "$WORKSPACE/terraform/gcp/backend.tf"
    terraform {
      backend "pg" {
        conn_str = "$TF_PG_CONN_STR"
      }
    }
EOF
  fi
  control_node "\
    terraform -chdir=$WORKSPACE/terraform/gcp/ init -upgrade -input=false
  "
}

# Delete workloads, cluster and workspace
function delete_cluster() {
  check_gcp_auth
  delete_x1
  delete_pvs
  delete_gke
  control_node "rm -rf /work/x1/$WORKSPACE"
}

function gcloud_login() {
  echo "This will store configuration in ~/.config/gcloud" 2>&1
  install -d ${HOME}/.config/gcloud
  control_node "set -x;
    if [[ -v GOOGLE_APPLICATION_CREDENTIALS ]]; then
      gcloud auth activate-service-account --key-file=\$GOOGLE_APPLICATION_CREDENTIALS
    else
      gcloud auth application-default login \
      && gcloud auth login
    fi
    gcloud config set --quiet project $X1_GCP_PROJECT_NAME"
}

function check_gpu_support() {
  control_node "export PYTHONPATH=/work/x1/src && (python -m infractl.deploy.gcp.main validate-gpu-settings $GPU_MODEL)"
}

if [[ -z "${X1_GCP_PROJECT_NAME}" ]];
then
  echo "Please set X1_GCP_PROJECT_NAME." >&2
  exit 1
fi

# This script is designed to work in the project root
cd "$PROJECT_ROOT"
allowed=(--help --console --check --render --deploy-gke --deploy-x1 --config --delete --delete-x1 --delete-gke --gcloud-login  --start-proxy --stop-proxy)
check_args "$@"

if [[ " $@ " =~ " --help " ]]; then
  show_help
  exit 0
fi

if [[ " $@ " =~ " --check " ]]; then
  control_node "curl https://ipinfo.io/"
  exit 0
fi

if [[ " $@ " =~ " --render " ]]; then
  set_gpu_type
  render_workspace
  exit 0
fi

if [[ " $@ " =~ " --deploy-gke " ]]; then
  if [[ "${GPU_ENABLED}" == "true" ]]; 
  then
    check_gpu_support
  fi
  deploy_gke
  exit 0
fi

if [[ " $@ " =~ " --config " ]]; then
  update_config
  exit 0
fi

if [[ " $@ " =~ " --deploy-x1 " ]]; then
  set_gpu_type
  deploy_x1
  exit 0
fi

if [[ " $@ " =~ " --delete " ]]; then
  delete_cluster
  exit 0
fi

if [[ " $@ " =~ " --delete-x1 " ]]; then
  set_gpu_type
  delete_x1
  exit 0
fi

if [[ " $@ " =~ " --delete-pvs " ]]; then
  delete_pvs
  exit 0
fi

if [[ " $@ " =~ " --delete-gke " ]]; then
  delete_gke
  exit 0
fi

if [[ " $@ " =~ " --gcloud-login " ]]; then
  gcloud_login
  exit 0
fi

if [[ " $@ " =~ " --start-proxy " ]]; then
  start_proxy
  exit $?
fi

if [[ " $@ " =~ " --stop-proxy " ]]; then
  stop_proxy
  exit $?
fi

if [[ " $@ " =~ " --print-workspace " ]]; then
  realpath "${WORKSPACE}"
  exit $?
fi

if [[ " $1 " =~ " --get-admin-token " ]]; then
  get_admin_token
  exit $?
fi

if [[ " $1 " =~ " --console " ]]; then
  shift
  _rest_args="$@"
  cmd="bash"
  if [[ -n "$_rest_args" ]]; then
    cmd="$_rest_args"
  else
    warn_about_proxy_and_variables
  fi
  control_node "$cmd"
  exit $?
fi

if [[ " $1 " =~ " --check-gpu-support " ]]; then
  check_gpu_support
  exit $?
fi

show_parameters
set_gpu_type
if [[ "${GPU_ENABLED}" == "true" ]]; 
then
  check_gpu_support
fi
render_workspace
deploy_gke
update_config
deploy_x1
get_admin_token
