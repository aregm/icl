## Terraform configuration for X1 Kubernetes workloads

## Prerequisites

The following binaries must be installed and added to `PATH`:
* `git`
* `kubectl`
* `helm`

The following environment variables must be set to the location of Kubernetes configuration file, usually `~/.kube/config`.
* `KUBE_CONFIG_PATH`
* `KUBECONFIG`

Note that the default context is used and currently there is no way to specify other context.
If a non-default context required, make a copy of the configuration file,
set the desired context as default one in this file.

## Applying

Before applying the Terraform configuration, use the following command to download the required providers:

```
terrafrom init
```

Applying the configuration to the cluster:

```
terraform apply
```
