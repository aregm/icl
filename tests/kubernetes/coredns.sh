#!/bin/bash

# Dumps a coredns logs and corefile.
# Creates logs/coredns-*.log in the current directory.

set -e

mkdir -p logs
rm -f logs/prefect-*.log

kubectl -n kube-system get cm coredns --template={{.data}} > logs/coredns-corefile.log

kubectl -n kube-system get pods -l k8s-app=kube-dns > logs/coredns-pods.log

kubectl -n kube-system get pods -l k8s-app=kube-dns --no-headers -o custom-columns=:metadata.name | while read -r coredns_pod; do
  echo "coredns-pod: $coredns_pod" >> logs/coredns-pods.log
  kubectl -n kube-system logs "$coredns_pod" >> logs/coredns-pods.log || true
done
