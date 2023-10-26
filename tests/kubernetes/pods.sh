#!/bin/bash

# Dumps a list of all pods and their statuses.
# Creates logs/pods.log in the current directory.

set -e

mkdir -p logs

kubectl get pods --all-namespaces > logs/pods.log
