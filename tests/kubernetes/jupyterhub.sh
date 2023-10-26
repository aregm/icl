#!/bin/bash

# Dumps jupyterhub logs.
# Creates logs/jupyterhub-* in the current directory.

set -e

mkdir -p logs
rm -f logs/jupyterhub-*.log

kubectl -n jupyterhub get pods > logs/jupyterhub-summary.log

kubectl -n jupyterhub get pods --no-headers -o custom-columns=:metadata.name -l component=hub | while read -r hub_pod; do
  echo "hub: $hub_pod" >> logs/jupyterhub-hub.log
  kubectl -n jupyterhub logs "$hub_pod" >> logs/jupyterhub-hub.log || true
done

kubectl -n jupyterhub get pods --no-headers -o custom-columns=:metadata.name -l component=singleuser-server | while read -r session_pod; do
  kubectl -n jupyterhub get pod "$session_pod" -o yaml >> logs/jupyterhub-sessions.log || true
  kubectl -n jupyterhub logs "$session_pod" -c notebook >> logs/jupyterhub-sessions.log || true
done
