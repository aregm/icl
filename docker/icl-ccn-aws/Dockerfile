ARG BASE_TAG

FROM $BASE_TAG

# Install aws cli to /usr/local/bin
RUN set -ex \
    && curl -sSLO https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
    && unzip awscli-exe-linux-x86_64.zip \
    && ./aws/install \
    && rm -rf awscli-exe-linux-x86_64.zip aws \
    && echo "complete -C '/usr/local/bin/aws_completer' aws" >> .bashrc

RUN set -ex \
    && chmod --recursive 0777 /work