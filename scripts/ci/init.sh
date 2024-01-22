#!/bin/sh

set -e
set -vx

set_env() {
    AGENT_ID=$(hostname | sed -e 's/.*[^0-9]//')
    AGENT_ID=${AGENT_ID:-100}

    WORKSPACE_DIR=$(dirname "$0")/../..
    WORKSPACE_DIR=$(cd "$WORKSPACE_DIR" && pwd -P)

    WORKFLOW_PREFIX=$(basename "$0" .sh)
    WORKFLOW_DIR="$WORKSPACE_DIR/$WORKFLOW_PREFIX"

    WORKFLOW_PREFIX_ID="$WORKFLOW_PREFIX-$AGENT_ID"

    X1_K8S_EXTRA_SETTINGS_FILE="$WORKSPACE_DIR/x1-cluster-profiles/profiles/ci.yaml"
    no_proxy=localtest.me,.localtest.me,$no_proxy

    VM_MEMORY=16384
    VM_CPU=8
    # Rocky Linux box is 8GB, expanding to 50GB.
    VM_DISK=50
    export VM_MEMORY VM_CPU VM_DISK

    export WORKSPACE_DIR
    export X1_K8S_EXTRA_SETTINGS_FILE
    export no_proxy
 
    echo "WORKFLOW_DIR: $WORKFLOW_DIR"
    echo "X1_K8S_EXTRA_SETTINGS_FILE: $X1_K8S_EXTRA_SETTINGS_FILE"
}

run_kind() {
    vm_start
    vm_exec ./x1/scripts/deploy/kind.sh
    vm_exec ./x1/scripts/deploy/kind.sh --console ./scripts/ccn/test.sh
    vm_cleanup
}

generate_key() (
    cd "$WORKFLOW_DIR"
    test -f ~/.ssh/id_rsa || ssh-keygen -q -b 2048 -t rsa -N '' -C 'cluster key' -f ~/.ssh/id_rsa
    mkdir -p generated
    ln -snf ~/.ssh/id_rsa generated/
    ln -snf ~/.ssh/id_rsa.pub generated/
)

set_env
generate_key
. "$WORKFLOW_DIR"/init.sh

vm_clean_before
trap vm_copy_logs EXIT

