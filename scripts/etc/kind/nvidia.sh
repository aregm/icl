#!/bin/bash

# This script needs to be executed in the kind control plane to setup NVIDIA.
# Works only with Debian Bookworm image.

export DEBIAN_FRONTEND=noninteractive
sed -i -E 's/^Components: .*$/Components: main non-free non-free-firmware contrib/g' /etc/apt/sources.list.d/debian.sources
apt-get update
apt-get install -y curl gnupg libc-bin pciutils psmisc apt-utils
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed "s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g" | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y --no-install-recommends nvidia-container-toolkit nvidia-smi nvidia-driver libcuda1
