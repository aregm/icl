#!/bin/bash

# This script executes smoke tests and must be executed on the control node.
# It loads .x1/environment file in the current directory, if exists, to set up environment variables.

# Usage: test.sh [option]
#   (no option)       installs dependencies and executes all tests
#   --dependencies    installs test dependencies
#   --tests           executes all tests

set -e

: ${ICL_INGRESS_DOMAIN:=localtest.me}

if [[ -f .x1/environment ]]; then
  source .x1/environment
fi

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd -- "$SCRIPT_DIR/../../" &> /dev/null && pwd )"

cd "$PROJECT_DIR"

: ${PREFECT_API_URL:="http://prefect.${ICL_INGRESS_DOMAIN}/api"}
: ${ICL_S3_ENDPOINT:="s3.${ICL_INGRESS_DOMAIN}"}
: ${ICL_RAY_ENDPOINT:="ray.${ICL_INGRESS_DOMAIN}:443"}

export PREFECT_API_URL
export PYTHONUNBUFFERED=1
export PATH=$HOME/.local/bin:$PATH
export PYTHONPATH="$PROJECT_DIR/src:$PROJECT_DIR/tests/smoke:$PROJECT_DIR/tests/integration"

function dependencies() {
  cd "$PROJECT_DIR"
  pip install --upgrade pip
  pip install .[integration_tests,ssh]
}

function dump_logs() {(
  cd "$PROJECT_DIR"
  # Each individual test can fail, this should not stop the whole process
  set +ex
  tests/kubernetes/pods.sh
  tests/kubernetes/coredns.sh
  tests/kubernetes/prefect.sh
  tests/kubernetes/jupyterhub.sh
)}

function smoke_check() {
  cd "$PROJECT_DIR/tests/smoke"
  echo "PREFECT_API_URL=$PREFECT_API_URL"
  echo "ICL_S3_ENDPOINT=$ICL_S3_ENDPOINT"
  echo "ICL_RAY_ENDPOINT=$ICL_RAY_ENDPOINT"
  pytest -v . \
    --s3-endpoint "$ICL_S3_ENDPOINT" \
    --ray-endpoint "$ICL_RAY_ENDPOINT"
}

function integration_tests() {
  # make sure ICL uses infrastructure address rather than PREFECT_API_URL
  unset PREFECT_API_URL
  cd "$PROJECT_DIR/tests/integration"
  # FIXME: temporary run tests sequentially, there is an issue with pytest-xdist and pytest-asyncio
  pytest -v . --address "$ICL_INGRESS_DOMAIN"
}

function test_all() {
  export ICL_LOGGING_TO_FILE="TRUE"
  smoke_check
  integration_tests
}

if (( $# == 0 )); then
  # Always dump logs, even when tests fail
  trap dump_logs EXIT
  dependencies
  test_all
  exit 0
fi

if [[ $1 == "--help" ]]; then
  # Print top-level comment in the beginning of this file as help.
  awk '/^# / { gsub("^# ", ""); print }' "$SCRIPT_DIR/test.sh"
  exit 0
fi

if [[ $1 == "--dependencies" ]]; then
  dependencies
  exit 0
fi

if [[ $1 == "--tests" ]]; then
  test_all
  exit 0
fi

echo "Unknown option: $1"
exit 1
