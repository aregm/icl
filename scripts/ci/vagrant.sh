#!/usr/bin/env bash

# This script is called from GitHub workflow.

. scripts/ci/init.sh

export X1_NOMAAS_CLUSTER_SUBNET_PREFIX=172.31.$AGENT_ID
export no_proxy=${X1_NOMAAS_CLUSTER_SUBNET_PREFIX}.0/24,$no_proxy

echo X1_LIBVIRT_DEFAULT_PREFIX: $X1_LIBVIRT_DEFAULT_PREFIX
echo X1_NOMAAS_CLUSTER_SUBNET_PREFIX: $X1_NOMAAS_CLUSTER_SUBNET_PREFIX

on_exit() {
    # To troubleshoot a failed workflow either comment out `vm_cleanup` below or add `sleep 60m`
    # to keep the virtual machines. For example:
    # [[ $? -eq 0 ]] || sleep 60m
    vm_copy_logs
    vm_cleanup
}

trap on_exit EXIT

vm_start
vm_exec ./everything.sh
vm_exec ./test.sh
