#!/bin/sh

dockerfile_before_context() {
    :
}

dockerfile_after_context() {
    :
}

docker_run() {
    docker run \
        -v "$agent_dir"/vagrant:/.vagrant.d -v /var/run/libvirt/:/var/run/libvirt/ \
        "$@"
}