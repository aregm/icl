ARG BASE_TAG

FROM $BASE_TAG

ARG GCLOUD_CLI_VERSION=426.0.0

RUN set -ex \
    && curl -sSL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_CLI_VERSION}-linux-$(uname -m).tar.gz | \
        tar -C /opt -zvxf - \
    && /opt/google-cloud-sdk/install.sh --usage-reporting=false -q \
    && echo "test -f /opt/google-cloud-sdk/completion.bash.inc && source /opt/google-cloud-sdk/completion.bash.inc" >> .bashrc

ENV PATH=${PATH}:/opt/google-cloud-sdk/bin

RUN set -ex \
    && gcloud components install --quiet gke-gcloud-auth-plugin \
    && chmod --recursive 0777 /work