FROM python:3.12-slim

ARG KUBECTL_VERSION=v1.28.2
ARG HELM_VERSION=v3.10.1
ARG TERRAFORM_VERSION=1.4.6

ENV HOME=/work

ENV PYTHONPATH=/work/x1:/work/x1/src

# Configuration file for kubectl
ENV KUBECONFIG=/work/.kube/config

# Configuration file for Terraform Kubernetes provider
ENV KUBE_CONFIG_PATH=/work/.kube/config

ENV PS1=control_node:\w\$
ENV PSX1=control_node:\w\$

WORKDIR /work

RUN set -ex \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
        bash-completion \
        ca-certificates \
        curl \
        dnsutils \
        git \
        iputils-ping \
        jq \
        less \
        openssh-client \
        unzip \
        vim \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies for Python scripts
# TODO: use consolidated list of dependencies for Python scripts
RUN pip install --no-cache-dir kubernetes boto3 pydantic click

# Install kubectl to /usr/local/bin
RUN \
    curl -sSL -o /usr/local/bin/kubectl https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl \
    && chmod 0755 /usr/local/bin/kubectl

# Install helm to /usr/local/bin
RUN \
    cd /usr/local/bin \
    && curl -sSL https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz -o - | tar --strip-components=1 -zxf - linux-amd64/helm

# Install terraform to /usr/local/bin
RUN \
    curl -sSLO https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin \
    && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

RUN set -ex \
    && echo "export PS1='control_node:\w\\$ '" >> .bashrc \
    && echo "source /etc/bash_completion" >> .bashrc \
    && echo "source <(kubectl completion bash)" >> .bashrc \
    && chmod --recursive 0777 /work

ENTRYPOINT ["/bin/bash"]
