# ICL cluster endpoints

There are two types of the ICL cluster endpoints:

* **External endpoints** accessible from the public network.
* **Internal endpoints** accessible from the cluster only, specifically from the containers running in the cluster.

Note that external endpoints are also accessible from the cluster.

## Kubernetes Dashboard

* External: http://dashboard.{ingress_domain}/

## Ceph Dashboard

* External: http://ceph.{ingress_domain}/

## Ceph S3 Endpoint

* Internal: http://rook-ceph-rgw-ceph-objectstore.rook-ceph/

## Grafana

* External: http://grafana.{ingress_domain}/

## JupyterHub

* External: http://jupyter.{ingress_domain}/

## VS Code Server

* External: http://vscode.{ingress_domain}/

## Prefect

* External: http://prefect.{ingress_domain}/

## Ray Dashboard

* External: http://{ingress_domain}/ray/

## Ray Client Endpoint

* Internal: ray://ray-head-svc.ray:10001/

## MinIO Console

* External: http://minio.{ingress_domain}/

## MinIO S3 Endpoint

* External: http://s3.{ingress_domain}/
* Internal: https://minio.minio/

## Dask Dashboard

* Internal: TODO

## Dask Client Endpoint

* Internal: TODO

## Docker Registry

* Internal (pods):  http://docker-registry.docker-registry:5000/
* Internal (nodes): http://127.0.0.1:5000/

# DNS configuration

For each cluster, there must be A or CNAME record for the subdomain that points to the external load balancer (LB) for the cluster, and a wildcard record that is CNAME for the subdomain.
Examples:

## External LB by name

```
test.example.com. 300 IN CNAME aws-elb-id.us-east-1.elb.amazonaws.com.
*.test.example.com. 300 IN CNAME test.example.com.
 
# Optional, ClearML requires its own subdomain.
*.clearml.test.example.com. 300 IN CNAME test.example.com.
```

## External LB by IP

```
test.example.com. 300 IN A 1.2.3.4
*.test.example.com. 300 IN CNAME test.example.com.
 
# Optional, ClearML requires its own subdomain.
*.clearml.test.example.com. 300 IN CNAME test.example.com.
```
