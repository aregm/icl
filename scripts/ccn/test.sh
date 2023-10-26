#!/bin/bash

# This script executes smoke tests and must be executed on the control node.
# It loads .x1/environment file in the current directory, if exists, to set up required environment variables:
#   INGRESS_DOMAIN

# Usage: test.sh [option]
#   (no option)       installs dependencies and executes all tests
#   --dependencies    installs test dependencies
#   --tests           executes all tests

set -e

: ${INGRESS_DOMAIN:=localtest.me}

if [[ -f .x1/environment ]]; then
  source .x1/environment
fi

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd -- "$SCRIPT_DIR/../../" &> /dev/null && pwd )"

cd "$PROJECT_DIR"

: ${PREFECT_API_URL:="http://prefect.${INGRESS_DOMAIN}/api"}
: ${S3_ENDPOINT:="s3.${INGRESS_DOMAIN}"}
: ${RAY_ENDPOINT:="ray.${INGRESS_DOMAIN}:443"}

export PREFECT_API_URL
export PYTHONUNBUFFERED=1
export PATH=$HOME/.local/bin:$PATH

function dependencies() {
  cd "$PROJECT_DIR"
  pip install .[integration_tests]
}

function dump_logs() {(
  cd "$PROJECT_DIR"
  # Each individual test can fail, this should not stop the whole process
  set +ex
  test/kubernetes/pods.sh
  test/kubernetes/coredns.sh
  test/kubernetes/prefect.sh
  test/kubernetes/jupyterhub.sh
)}

function smoke_check() {
  cd "$PROJECT_DIR/test/smoke"
  echo "PREFECT_API_URL=$PREFECT_API_URL"
  echo "S3_ENDPOINT=$S3_ENDPOINT"
  echo "RAY_ENDPOINT=$RAY_ENDPOINT"
  pytest -v . \
    --s3-endpoint $S3_ENDPOINT \
    --ray-endpoint $RAY_ENDPOINT
}

function integration_tests() {
  cd "$PROJECT_DIR/test/integration"
  pytest -n 4 -v . --address $INGRESS_DOMAIN
}

function test_all() {
  export X1_LOGGING_TO_FILE="TRUE"
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
