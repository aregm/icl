#!/usr/bin/env bash

# Deploys ICL cluster to AWS

set -e

# Default values that can be overriden by corresponding environment variables
: ${X1_CLUSTER_NAME:="x1-$USER"}
: ${AWS_DEFAULT_REGION:="us-east-1"}
: ${X1_CLUSTER_VERSION:="1.28"}
: ${X1_EXTERNALDNS_ENABLED:="false"}
: ${CONTROL_NODE_IMAGE:="pbchekin/icl-ccn-aws:0.0.1"}
: ${ICL_INGRESS_DOMAIN:="test.x1infra.com"}

# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$SCRIPT_DIR/functions.sh"

export AWS_DEFAULT_REGION
# workspace is relative to PROJECT_ROOT
WORKSPACE="workspace/$X1_CLUSTER_NAME"
KUBECONFIG="$PROJECT_ROOT/$WORKSPACE/kubeconfig"

function show_help() {
  cat <<EOF
Usage: $(basename $0) [option]

Options:
  --help              Show this help
  --console           Start control node console
  --check             Run a quick check for Docker and network connectivity
  --render            Create workspace directory
  --deploy-eks        Deploy EKS cluster only
  --deploy-x1         Deploy X1 workloads only
  --config            Generate Kubernetes config
  --delete            Delete workloads, cluster and workspace
  --delete-x1         Delete X1 workloads only
  --delete-eks        Delete EKS cluster only
  --start-proxy       Start a proxy container
  --stop-proxy        Stop a proxy container

Environment variables:
  X1_CLUSTER_NAME     Cluster name, must be unique in AWS region, default is x1-$USER
EOF
}

function show_parameters() {
  for var in ICL_INGRESS_DOMAIN AWS_DEFAULT_REGION WORKSPACE; do
    echo "$var: ${!var}"
  done
}

function render_eks_terraform_tfvars() {
  cat <<EOF >> "$WORKSPACE/terraform/aws/terraform.tfvars"
cluster_name = "$X1_CLUSTER_NAME"
cluster_version = "$X1_CLUSTER_VERSION"
EOF
}

function x1_terraform_args() {
  terraform_extra_args=(
    -var prometheus_enabled=false
    -var ingress_domain="${ICL_INGRESS_DOMAIN}"
    -var ingress_nginx_service_enabled=true
    -var local_path_enabled=false # use EBS CSI for EKS instead
    -var default_storage_class="gp2"
    -var externaldns_enabled="${X1_EXTERNALDNS_ENABLED}"
    -var ray_load_balancer_enabled=true # dedicated AWS CLB for Ray client endpoint on port 80
    -var use_node_ip_for_user_ports=true
    -var use_external_node_ip_for_user_ports=true
  )
  echo "${terraform_extra_args[*]}"
}


function deploy_eks() {
  control_node "terraform -chdir=$WORKSPACE/terraform/aws/ apply -input=false -auto-approve"
}

function update_config() {
  control_node "aws eks update-kubeconfig --name $X1_CLUSTER_NAME --alias $X1_CLUSTER_NAME"
}

# Delete cluster
function delete_eks() {
  control_node "terraform -chdir=$WORKSPACE/terraform/aws/ destroy -input=false -auto-approve"
}

# Delete workloads, cluster and workspace
function delete_cluster() {
  delete_x1
  delete_pvs
  delete_eks
  control_node "rm -rf /work/x1/$WORKSPACE"
}

# Create workspace
# TODO: move to infractl.deploy.aws
function render_workspace() {
  mkdir -p "$PROJECT_ROOT/$WORKSPACE/terraform/aws"
  touch "$KUBECONFIG"
  control_node "\
    export PYTHON_PATH=/work/x1/src \
    && cp -r /work/x1/terraform/aws/* /work/x1/$WORKSPACE/terraform/aws/ \
    && ( python -m infractl.deploy.aws.main print-vpc-tfvars > /work/x1/$WORKSPACE/terraform/aws/terraform.tfvars ) \
    && terraform -chdir=$WORKSPACE/terraform/aws/ init -input=false
  "
  render_eks_terraform_tfvars
}

# This script is designed to work in the project root
cd "$PROJECT_ROOT"
allowed=(--help --console --check --render --deploy-eks --deploy-x1 --config --delete --delete-x1 --delete-eks --start-proxy --stop-proxy)
check_args "$@"

if [[ " $@ " =~ " --help " ]]; then
  show_help
  exit 0
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

if [[ " $@ " =~ " --check " ]]; then
  control_node "curl https://ipinfo.io/"
  exit 0
fi

if [[ " $@ " =~ " --render " ]]; then
  render_workspace
  exit 0
fi

if [[ " $@ " =~ " --deploy-eks " ]]; then
  deploy_eks
  exit 0
fi

if [[ " $@ " =~ " --config " ]]; then
  update_config
  exit 0
fi

if [[ " $@ " =~ " --deploy-x1 " ]]; then
  deploy_x1
  exit 0
fi

if [[ " $@ " =~ " --delete " ]]; then
  delete_cluster
  exit 0
fi

if [[ " $@ " =~ " --delete-x1 " ]]; then
  delete_x1
  exit 0
fi

if [[ " $@ " =~ " --delete-pvs " ]]; then
  delete_pvs
  exit 0
fi

if [[ " $@ " =~ " --delete-eks " ]]; then
  delete_eks
  exit 0
fi

if [[ " $@ " =~ " --start-proxy " ]]; then
  start_proxy
  exit 0
fi

if [[ " $1 " =~ " --get-admin-token " ]]; then
  get_admin_token
  exit $?
fi

if [[ " $@ " =~ " --stop-proxy " ]]; then
  stop_proxy
  exit 0
fi

show_parameters
render_workspace
deploy_eks
update_config
deploy_x1
get_admin_token