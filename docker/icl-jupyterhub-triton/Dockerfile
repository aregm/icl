ARG BASE_TAG

FROM pbchekin/icl-jupyterhub:0.0.22

USER root

RUN set -ex; \
    export DEBIAN_FRONTEND=noninteractive; \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy unified' > /etc/apt/sources.list.d/intel-gpu-jammy.list; \
    curl -sSL https://repositories.intel.com/gpu/intel-graphics.key | gpg --dearmor --output /usr/share/keyrings/intel-graphics.gpg; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends --fix-missing \
      intel-opencl-icd \
      clinfo \
      intel-opencl-icd intel-level-zero-gpu libze1 \
      intel-media-va-driver-non-free libmfx1 libmfxgen1 libvpl2 libigdgmm12 \
      libigc-dev intel-igc-cm libigdfcl-dev libigfxcmrt-dev libze-dev \
      intel-ocloc intel-ocloc-dev \
      \
      build-essential \
      zlib1g-dev \
      cmake \
      ninja-build \
      ncurses-term \
      pkg-config \
      \
      libpng-dev libjpeg-dev libsndfile1-dev libxml2-dev libxslt1-dev \
      fontconfig libfontconfig1-dev \
      libpango-1.0-0 libpangoft2-1.0-0 \
      \
      gh \
    ; \
    apt-get install -y --no-install-recommends --fix-missing \
      libgl1 \
    ; \
    apt-get install -y --no-install-recommends --fix-missing \
      wget \
      zsh \
    ; \
    rm -rf /var/lib/apt/lists/*

RUN set -ex; \
    curl -sSLO https://registrationcenter-download.intel.com/akdlm/IRC_NAS/5b4aa67a-9679-4d02-865b-137d0f767d82/intel-deep-learning-essentials-2025.0.0.345_offline.sh; \
    /bin/sh intel-deep-learning-essentials*.sh -a --silent --eula accept; \
    echo intel-deep-learning-essentials*.sh > /opt/intel/installed.txt; \
    rm intel-deep-learning-essentials*.sh

USER ${USER}