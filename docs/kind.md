# Deploying a local ICL cluster

## Prerequisites:

* Docker installed.
* Firewall allows connections to arbitrary ports from localhost to localhost and Docker network.

In Windows, WSL (Windows Subsystem for Linux) version 1.1.2.0 or newer (version 1.1.0.0 has a bug with port forwarding https://github.com/microsoft/WSL/issues/9508).

## Create a local ICL cluster

```
./scripts/deploy/kind.sh
```

## Access cluster

The cluster's endpoints are accessible only from localhost.
In your browser, navigate to http://jupyter.localtest.me.
When using an HTTP proxy make sure domain `localtest.me` is included in the "no proxy" list.

When the script completes, it creates and configures a Kubernetes default context,
so if you have `kubectl` installed you can use it to access the cluster, for example:

```
kubectl get namespaces
```

## Control node

"Control node" is a Docker container that contains pre-installed tools,
such as `kubectl`, `helm`, `terraform`, and that is configured to access the cluster.
To run the control node:

```
source ./scripts/deploy/functions.sh

# runs bash inside the control node
control_node

# runs a command inside the control node
control_node "kubectl get namespaces"
```

## Delete a local ICL cluster

```
./scripts/deploy/kind.sh --delete
```

## Advanced scenarios

### Cluster with NVIDIA GPU support

The following command passes the existing `/dev/nvidia*` devices to the cluster and installs the required dependencies:

```shell
./scripts/deploy/kind.sh --with-nvidia
```

To verify that NVIDIA GPU works in the cluster execute:

```shell
cat <<EOF | kubectl create -f -
 apiVersion: v1
 kind: Pod
 metadata:
   name: vector-add
 spec:
   restartPolicy: OnFailure
   containers:
   - name: vector-add
     image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
     resources:
       limits:
          nvidia.com/gpu: 1
EOF
```

Check the logs:

```shell
kubectl logs vector-add
```

If NVIDIA GPU works in the cluster you will see the following output:

```
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done
```

### Control node console

The following command starts an ephemeral control node in a Docker container and starts a new Bash session:

```shell
./scripts/deploy/kind.sh --console
```

The Kubernetes context is configured in that control node,
so you can use `kubectl`, `helm` and so on in that Bash session.

### Use pre-pulled Docker images

Pull the required Docker images locally:

```
./scripts/deploy/kind.sh --pull-images
```

Start a cluster and load pre-pulled Docker images to speed up the deployment:

```
./scripts/deploy/kind.sh --with-images
```

### HTTP and HTTPS proxies

The script uses the following environment variables if they are set:

* `http_proxy`
* `https_proxy`
* `no_proxy`

Note that if HTTP proxy is set via `http_proxy`,
the deployment script sets up a transparent HTTP proxy and forwards all external connections from a cluster to ports 80 and 443 through that proxy.
Currently, script does not support a case when HTTPS proxy differs from HTTP proxy.

### DockerHub proxy

To avoid `429 Too Many Requests` error from DockerHub Registry `docker.io`, it is possible to use a DockerHub proxy/cache.
To enable it, set the following environment variable:

* `dockerhub_proxy`

Use the host name, scheme `https` and port `443` are assumed and must be skipped at the moment.
For example:

```
export dockerhub_proxy=dockerhubregistry.example.com
```

### Tests

```shell
./scripts/deploy/kind.sh --console

# On control node execute
./scripts/ccn/test.sh
```
