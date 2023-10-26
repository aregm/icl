#!/bin/bash

# Dumps prefect logs.
# Creates logs/prefect-* in the current directory.

set -e

mkdir -p logs
rm -f logs/prefect-*.log

kubectl -n prefect get pods --no-headers -o custom-columns=:metadata.name -l app.kubernetes.io/component=server | while read -r prefect_server_pod; do
  echo "prefect-server: $prefect_server_pod" >> logs/prefect-summary.log
  echo "prefect-server: $prefect_server_pod" >> logs/prefect-server.log
  kubectl -n prefect logs "$prefect_server_pod" >> logs/prefect-server.log || true
done

kubectl -n default get pods --no-headers -o custom-columns=:metadata.name -l app.kubernetes.io/component=agent | while read -r prefect_agent_pod; do
  echo "prefect-agent: $prefect_agent_pod" >> logs/prefect-summary.log
  echo "prefect-agent: $prefect_agent_pod" >> logs/prefect-agent.log
  kubectl -n default logs "$prefect_agent_pod" >> logs/prefect-agent.log
done

kubectl -n default get jobs > logs/prefect-jobs.log
kubectl -n default get pods > logs/prefect-pods.log

kubectl -n default get jobs --no-headers -o custom-columns=:metadata.name | while read -r prefect_job; do
  echo "prefect-job: $prefect_job" >> logs/prefect-summary.log
  kubectl -n default get pods --no-headers -o custom-columns=:metadata.name -l job-name="$prefect_job" | while read -r prefect_pod; do
    echo "prefect-pod: $prefect_pod" >> logs/prefect-summary.log
    if [[ $prefect_pod ]]; then
      echo "prefect-pod: $prefect_pod" >> logs/prefect-pods.log
      kubectl -n default logs "$prefect_pod" -c prefect-job >> logs/prefect-pods.log || true
    fi
  done
done
