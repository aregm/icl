#!/bin/bash

# Starts a containerized control node and uses it to deploy a cluster.

set -e

source ./functions.sh

control_node ./scripts/ccn/everything.sh

# Start nginx on port 80 as a load balancer for the endpoints.
nginx_start

# Start coredns to resolve the endpoints outside of the cluster.
coredns_start
