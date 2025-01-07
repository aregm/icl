FROM vagrantlibvirt/vagrant-libvirt:0.10.7

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
        libicu-dev \
        git \
        python3-pip \
        python3-dev \
        virtinst \
        socat \
        && \
    apt-get clean

RUN pip --no-cache-dir install ansible==6.4.0 jmespath libvirt-python lxml
RUN ansible-galaxy collection install community.libvirt
