#!/bin/bash

# This script deploys Kubernetes, ICL and must be executed on the control node.
# TODO: Support command line options to make each step independently.

set -e

# Do not display skipped task/host entries
export ANSIBLE_DISPLAY_SKIPPED_HOSTS=False

cd ~/kubespray
ansible-playbook --inventory ~/generated/kubespray-inventory/inventory.yaml --become cluster.yml

cd ~/x1
ansible-playbook --inventory ~/generated/kubespray-inventory/inventory.yaml ansible/playbooks/fetch-kubeconfig.yaml
ansible-playbook --inventory ~/generated/kubespray-inventory/inventory.yaml ansible/playbooks/terraform_tfvars.yaml

cd ~/x1/terraform/icl
terraform init -input=false
terraform apply -input=false -auto-approve -var-file ~/generated/terraform.tfvars
