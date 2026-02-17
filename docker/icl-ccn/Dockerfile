FROM python:3.12-slim

ARG KUBECTL_VERSION=v1.28.2
ARG HELM_VERSION=v3.10.1
ARG TERRAFORM_VERSION=1.4.6

# BuildKit-provided args (set automatically by docker buildx)
ARG TARGETOS
ARG TARGETARCH

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
RUN pip install --no-cache-dir kubernetes boto3 pydantic click

# Resolve tool arch names once
RUN set -ex \
  && : "${TARGETOS:=linux}" \
  && case "${TARGETARCH}" in \
       amd64) TOOL_ARCH=amd64 ;; \
       arm64) TOOL_ARCH=arm64 ;; \
       *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
     esac \
  && echo "Using TARGETOS=${TARGETOS} TARGETARCH=${TARGETARCH} TOOL_ARCH=${TOOL_ARCH}" \
  && curl -sSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/${TARGETOS}/${TOOL_ARCH}/kubectl" \
  && chmod 0755 /usr/local/bin/kubectl \
  && cd /usr/local/bin \
  && curl -sSL "https://get.helm.sh/helm-${HELM_VERSION}-${TARGETOS}-${TOOL_ARCH}.tar.gz" -o - | tar --strip-components=1 -zxf - "${TARGETOS}-${TOOL_ARCH}/helm" \
  && curl -sSLo "/tmp/terraform.zip" "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${TARGETOS}_${TOOL_ARCH}.zip" \
  && unzip /tmp/terraform.zip -d /usr/local/bin \
  && rm /tmp/terraform.zip

RUN set -ex \
    && echo "export PS1='control_node:\w\\$ '" >> .bashrc \
    && echo "source /etc/bash_completion" >> .bashrc \
    && echo "source <(kubectl completion bash)" >> .bashrc \
    && chmod --recursive 0777 /work

ENTRYPOINT ["/bin/bash"]
