#!/bin/sh

set -e
set -vx

set_env() {
    AGENT_ID=$(hostname | sed -e 's/.*[^0-9]//')
    export AGENT_ID=${AGENT_ID:-100}

    WORKSPACE_DIR=$(dirname "$0")/../..
    export WORKSPACE_DIR=$(cd "$WORKSPACE_DIR" && pwd -P)

    export X1_PREFIX=$(basename "$0" .sh)
    export X1_VAGRANT_DIR="$WORKSPACE_DIR/$X1_PREFIX"

    export X1_LIBVIRT_DEFAULT_PREFIX="$X1_PREFIX-$AGENT_ID"
    export VAGRANT_DEFAULT_PROVIDER=libvirt
    export X1_K8S_EXTRA_SETTINGS_FILE="$WORKSPACE_DIR/x1-cluster-profiles/profiles/ci.yaml"
    export no_proxy=localtest.me,.localtest.me,$no_proxy

    echo "PWD: $PWD"
    echo "WORKSPACE_DIR: $WORKSPACE_DIR"
    echo "X1_LIBVIRT_DEFAULT_PREFIX: $X1_LIBVIRT_DEFAULT_PREFIX"
    echo "X1_K8S_EXTRA_SETTINGS_FILE: $X1_K8S_EXTRA_SETTINGS_FILE"
}

start_vagrant() {
    echo "Starting up Vagrant VMs ..."

    cd "$X1_VAGRANT_DIR"
    vagrant up
}

function cleanup {
    cd "$X1_VAGRANT_DIR"
    echo "Copying logs ..."
    vagrant scp jumphost:x1/logs "$WORKSPACE_DIR" || true
    echo "Cleaning up Vagrant VMs ..."
    vagrant destroy -f || true
}

clean_all() {
    cd "$X1_VAGRANT_DIR"

    ps -ef
    echo "Cleaning vagrant"
    vagrant destroy -f || true

    echo "Cleaning domains"
    virsh list --all
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh destroy || true
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh undefine || true

    echo "Cleaning nets"
    virsh net-list --all
    virsh net-destroy "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true
    virsh net-undefine "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true

    echo "Cleanup finished"
}

generate_key() {
    test -f ~/.ssh/id_rsa || ssh-keygen -q -b 2048 -t rsa -N '' -C 'cluster key' -f ~/.ssh/id_rsa
    mkdir -p generated
    ln -snf ~/.ssh/id_rsa generated/
    ln -snf ~/.ssh/id_rsa.pub generated/
}

ensure_vagrant_plugins() {
    if ! vagrant plugin list | grep -q vagrant-proxyconf; then
        vagrant plugin install vagrant-proxyconf
    fi
    if ! vagrant plugin list | grep -q vagrant-reload; then
        vagrant plugin install vagrant-reload
    fi
    if ! vagrant plugin list | grep -q vagrant-scp; then
        vagrant plugin install vagrant-scp
    fi
}

set_env
ensure_vagrant_plugins
clean_all
generate_key

trap cleanup EXIT

