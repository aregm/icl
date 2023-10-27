#!/bin/bash

# Starts a containerized control node and uses it to run smoke tests.

set -e

source ./functions.sh

control_node ./scripts/ccn/test.sh
