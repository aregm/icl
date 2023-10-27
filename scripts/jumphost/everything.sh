#!/bin/bash

# Starts a containerized control node and uses it to deploy Kubernetes and X1.

set -e

source ./functions.sh

control_node ./scripts/ccn/everything.sh

# Start nginx on port 80 as a load balancer for X1 endpoints.
nginx_start

# Start coredns to resolve X1 endpoints outside of the cluster.
coredns_start
