ARG BASE_TAG

FROM ${BASE_TAG}

USER root

RUN set -ex; \
    export DEBIAN_FRONTEND=noninteractive; \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy unified' > /etc/apt/sources.list.d/intel-gpu-jammy.list; \
    curl -s https://repositories.intel.com/gpu/intel-graphics.key | gpg --dearmor --output /usr/share/keyrings/intel-graphics.gpg; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends --fix-missing \
      intel-opencl-icd \
      clinfo \
      intel-level-zero-gpu \
      level-zero \
      level-zero-dev libigc-dev intel-igc-cm libigdfcl-dev libigfxcmrt-dev \
    ; \
    rm -rf /var/lib/apt/lists/*

USER ${USER}

ENV LD_LIBRARY_PATH=/opt/intel/oneapi/lib:/opt/intel/oneapi/lib/intel64:$LD_LIBRARY_PATH