ARG BASE_TAG

FROM python:3.12-bookworm as python_builder

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/

COPY src/infractl/ /app/src/infractl/

RUN set -ex; \
    pip install .[build]; \
    python -m build

FROM prefecthq/prefect:$BASE_TAG

ARG MODIN_VERSION
ARG RAY_VERSION

COPY --from=python_builder /app/dist/*.whl /opt/icl/dist/

RUN set -ex; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends git ca-certificates curl gnupg; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
    chmod a+r /etc/apt/keyrings/docker.gpg; \
    . /etc/os-release; \
    echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian "$VERSION_CODENAME" stable" > /etc/apt/sources.list.d/docker.list; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends docker-ce-cli; \
    rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

RUN pip --no-cache-dir install minio s3fs s3cmd /opt/icl/dist/*.whl

# MODIN_VERSION and RAY_VERSION are optional: when not set, Modin and Ray are not installed and
# can be added in runtime with EXTRA_PIP_PACKAGES.
RUN \
    if [[ -n "$RAY_VERSION" ]]; then \
      pip --no-cache-dir install ray==${RAY_VERSION}; \
    fi; \
    if [[ "$MODIN_VERSION" = *git* ]]; then \
      pip --no-cache-dir install "modin[ray] @ ${MODIN_VERSION}"; \
    elif [[ -n "$MODIN_VERSION" ]]; then \
      pip --no-cache-dir install "modin[ray]==${MODIN_VERSION}"; \
    fi