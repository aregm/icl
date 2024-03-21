#!/bin/sh

vm_start() {
    local rsa_key
    local vm_ip

    cd "$WORKFLOW_DIR"
    rsa_key=$(cat ~/.ssh/id_rsa.pub)

    cat <<EOF >cloud-init.yaml
#cloud-config
ssh_authorized_keys:
  - $rsa_key

fqdn: jumphost

runcmd:
  - apt update && apt upgrade -y
EOF

    cat <<EOF >ansible.cfg
[defaults]
host_key_checking = False
EOF

    # Fix ERROR: Ansible could not initialize the preferred locale: unsupported locale setting
    export LC_ALL="C.UTF-8"
    locale

    multipass launch --name "vm-$WORKFLOW_PREFIX_ID" -m "$VM_MEMORY"M -c "$VM_CPU" -d "$VM_DISK"G --cloud-init=./cloud-init.yaml rocky

    vm_ip=$(multipass info "vm-$WORKFLOW_PREFIX_ID" | awk '/^IPv4: / { print $2 }')
    ansible-playbook --inventory ubuntu@$vm_ip, --extra-vars "@$X1_K8S_EXTRA_SETTINGS_FILE" jumphost.yaml
}

vm_exec() {
    multipass exec "vm-$WORKFLOW_PREFIX_ID" -- "$@"
}

vm_copy_logs() {
    echo "Copying logs ..."
    cd "$WORKFLOW_DIR"
    multipass transfer --recursive --parents "vm-$WORKFLOW_PREFIX_ID":x1/logs "$WORKSPACE_DIR" || true
}

vm_clean_before() {
    multipass delete -p "vm-$WORKFLOW_PREFIX_ID" || true
}

vm_cleanup() {
    vm_clean_before
}


