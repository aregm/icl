FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    lsb-release \
    software-properties-common \
    qemu-utils qemu-utils qemu-system ovmf cloud-image-utils packer libnbd-bin nbdkit fuse2fs \
    fuse3 gettext-base \
    --

RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
    apt-get update && apt-get install packer

ARG KVM_GID
RUN useradd -m --uid 1002 ghrunner && groupadd -g $KVM_GID kvm && usermod -a -G kvm ghrunner

USER ghrunner
WORKDIR /home/ghrunner

