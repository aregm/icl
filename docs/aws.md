# Deploy X1 to AWS

## Prerequisites

* Docker 
* Credentials to access AWS account:

    ```shell
    export AWS_ACCESS_KEY_ID="..."
    export AWS_SECRET_ACCESS_KEY="..."
    export AWS_SESSION_TOKEN="..."
    ```

* AWS region needs to be specified in environment variable `AWS_DEFAULT_REGION`, for example:

    ```shell
    export AWS_DEFAULT_REGION="us-east-1"
    ```

* In the specified AWS account and region, a default VPC must exist with at least 2 default subnets for different availability zones.

## Deploy X1 cluster

```shell
./scripts/deploy/aws.sh
```

## Delete X1 cluster

```shell
./scripts/deploy/aws.sh --delete
```

## Advanced scenarios

### Control node console

The following command starts an ephemeral control node in a Docker container and starts a new Bash session:   

```shell
./scripts/deploy/aws.sh --console
```

The Kubernetes context is configured in that control node,
so you can use `kubectl`, `helm` and so on in that Bash session. 

### HTTP and HTTPS proxies

The script uses the following environment variables if they are set:

* `http_proxy`
* `https_proxy`
* `no_proxy`

Note that the proxy is only used by the script itself, it is not used in the cluster.

To run console with transparent proxy in a sidecar container:

```shell
./scripts/deploy/aws.sh --start-proxy
./scripts/deploy/aws.sh --console
./scripts/deploy/aws.sh --stop-proxy
```

### Cluster authentication

When you create an Amazon EKS cluster, the IAM principal that creates the cluster is automatically granted `system:masters` permissions.
To grant additional IAM principals the ability to interact with your cluster, edit the `kube-syste/aws-auth` ConfigMap.

Example:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::980842202052:role/main-eks-node-group-20230119212622560000000001
      groups:
        - system:bootstrappers
        - system:nodes
      username: system:node:{{EC2PrivateDNSName}}

    - rolearn: arn:aws:iam::980842202052:role/AWSReservedSSO_AWSAdministratorAccess_bf7da1573ba8f7c9
      username: system:node:{{SessionName}}
      groups:
        - system:masters
```

See also:

* https://docs.aws.amazon.com/eks/latest/userguide/cluster-auth.html
* https://docs.aws.amazon.com/eks/latest/userguide/default-roles-users.html

### DNS

To access the cluster endpoints you need to configure an external DNS and set up the following
records:

```shell
{ingess_domain}. 300 IN CNAME {ingress_nginx_elb}.
*.{ingess_domain}. 300 IN CNAME {ingess_domain}.

# Optional, Ray client endpoint uses a dedicated AWS ELB.
ray-api.{ingess_domain}. 300 IN CNAME {ray_elb}.
 
# Optional, ClearML requires its own subdomain.
*.clearml.{ingess_domain}. 300 IN CNAME {ingess_domain}.
```

Where

* `{ingess_domain}` is the cluster ingress domain, specified as a parameter for cluster creation.
* `{ingress_nginx_elb}` is a DNS name of AWS CLB tagged with `kubernetes.io/service-name = ingress-nginx/ingress-nginx-controller`.
* `{ray_elb}` is a DNS name of AWS CLB tagged with `kubernetes.io/service-name = ray/ray-client`.

### Tests

```shell
# Optional, use only when X1 endpoints are accessible via HTTP proxy
./scripts/deploy/aws.sh --start-proxy

./scripts/deploy/aws.sh --console

# On control node execute
export X1_INGRESS_DOMAIN=test.x1infra.com
export X1_RAY_ENDPOINT=ray-api.test.x1infra.com:80
./scripts/ccn/test.sh

# Optional, use only when X1 endpoints are accessible via HTTP proxy
./scripts/deploy/aws.sh --stop-proxy
```
