#!/usr/bin/env bash

# This script is called from GitHub workflow.
# Single node ICL cluster with Kind on Vagrant VM with Rocky Linux.

set -e

export WORKSPACE_DIR="$GITHUB_WORKSPACE"
export X1_LIBVIRT_DEFAULT_PREFIX="github-${GITHUB_RUN_ID}"
export VAGRANT_DEFAULT_PROVIDER=libvirt
export X1_K8S_EXTRA_SETTINGS_FILE="$WORKSPACE_DIR/x1-cluster-profiles/profiles/ci.yaml"

function cleanup {
  cd "$WORKSPACE_DIR/vagrant-rl-kind"
  echo "Copying logs ..."
  vagrant scp jumphost:x1/logs "$WORKSPACE_DIR" || true
  echo "Cleaning up Vagrant VMs ..."
  vagrant destroy -f || true
}

cd "$WORKSPACE_DIR/vagrant-rl-kind"
. "$WORKSPACE_DIR/scripts/ci/init.sh"

trap cleanup EXIT

echo "PWD: $PWD"
echo "WORKSPACE_DIR: $WORKSPACE_DIR"
echo "X1_LIBVIRT_DEFAULT_PREFIX: $X1_LIBVIRT_DEFAULT_PREFIX"
echo "X1_K8S_EXTRA_SETTINGS_FILE: $X1_K8S_EXTRA_SETTINGS_FILE"

echo "Starting up Vagrant VMs ..."

cd "$WORKSPACE_DIR/vagrant-rl-kind"
vagrant up
vagrant ssh jumphost -c "./x1/scripts/deploy/kind.sh"
vagrant ssh jumphost -c "./x1/scripts/deploy/kind.sh --console ./scripts/ccn/test.sh"
