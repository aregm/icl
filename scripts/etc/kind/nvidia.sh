#!/bin/bash

# This script needs to be executed in the kind control plane to setup NVIDIA.
# Works only with Debian Bookworm image.

set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl gnupg libc-bin pciutils psmisc apt-utils

curl -fsSLO https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get install -y --no-install-recommends nvidia-driver cuda-drivers nvidia-container-toolkit

nvidia-smi
