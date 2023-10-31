#!/bin/bash

# This script executes smoke tests and must be executed on the control node.
# It loads .x1/environment file in the current directory, if exists, to set up environment variables.

# Usage: test.sh [option]
#   (no option)       installs dependencies and executes all tests
#   --dependencies    installs test dependencies
#   --tests           executes all tests

set -e

: ${X1_INGRESS_DOMAIN:=localtest.me}

if [[ -f .x1/environment ]]; then
  source .x1/environment
fi

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd -- "$SCRIPT_DIR/../../" &> /dev/null && pwd )"

cd "$PROJECT_DIR"

: ${PREFECT_API_URL:="http://prefect.${X1_INGRESS_DOMAIN}/api"}
: ${X1_S3_ENDPOINT:="s3.${X1_INGRESS_DOMAIN}"}
: ${X1_RAY_ENDPOINT:="ray.${X1_INGRESS_DOMAIN}:443"}

export PREFECT_API_URL
export PYTHONUNBUFFERED=1
export PATH=$HOME/.local/bin:$PATH
export PYTHONPATH="$PROJECT_DIR/src:$PROJECT_DIR/tests/smoke:$PROJECT_DIR/tests/integration"

function dependencies() {
  cd "$PROJECT_DIR"
  pip install .[integration_tests]
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
  echo "X1_S3_ENDPOINT=$X1_S3_ENDPOINT"
  echo "X1_RAY_ENDPOINT=$X1_RAY_ENDPOINT"
  pytest -v . \
    --s3-endpoint $X1_S3_ENDPOINT \
    --ray-endpoint $X1_RAY_ENDPOINT
}

function integration_tests() {
  cd "$PROJECT_DIR/tests/integration"
  pytest -n 4 -v . --address $X1_INGRESS_DOMAIN
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
