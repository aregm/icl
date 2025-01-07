ARG BASE_TAG

FROM rayproject/ray:$BASE_TAG

ARG MODIN_VERSION

SHELL ["/bin/bash", "-c"]

#RUN $HOME/anaconda3/bin/pip --no-cache-dir install -U s3fs "modin[ray] @ ${MODIN_VERSION}"; \
RUN pip --no-cache-dir install -U s3fs "modin[ray]==${MODIN_VERSION}";
    