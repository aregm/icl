#!/bin/sh

vm_start() {
    echo "Starting up Vagrant VMs ..."

    cd "$WORKFLOW_DIR"
    vagrant up        
}

vm_exec() {
    local cmd

    cmd=$@
    vagrant ssh jumphost -c "$cmd"
}

vm_copy_logs() {
    echo "Copying logs ..."
    cd "$WORKFLOW_DIR"
    vagrant scp jumphost:x1/logs "$WORKSPACE_DIR" || true
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

set_vagrant_env() {
    export X1_LIBVIRT_DEFAULT_PREFIX="$WORKFLOW_PREFIX_ID"
    export VAGRANT_DEFAULT_PROVIDER=libvirt
}

vm_clean_before() {
    echo "Cleaning up Vagrant VMs ..."
    cd "$WORKFLOW_DIR"

    ps -ef
    echo "Cleaning vagrant"
    vagrant destroy -f || true

    echo "Cleaning domains"
    virsh list --all
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh destroy || true
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh undefine --remove-all-storage || true

    echo "Cleaning nets"
    virsh net-list --all
    virsh net-destroy "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true
    virsh net-undefine "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true

    echo "Cleanup finished"
}

vm_cleanup() {
    vm_clean_before
}

ensure_vagrant_plugins
set_vagrant_env

