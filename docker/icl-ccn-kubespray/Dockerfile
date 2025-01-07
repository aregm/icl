ARG BASE_TAG

FROM $BASE_TAG

ARG KUBESPRAY_REPO=https://github.com/kubernetes-sigs/kubespray.git
ARG KUBESPRAY_VERSION=v2.24.1

RUN set -ex \
    && git clone --config advice.detachedHead=false --quiet --depth 1 --branch ${KUBESPRAY_VERSION} ${KUBESPRAY_REPO} \
    && cd kubespray \
    && pip install --no-cache-dir -r requirements.txt