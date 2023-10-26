# Build

ICL build API allows building custom Docker images and pushing them to a Docker registry.

The main features of the API:

* It leverages the existing local Docker, if exists.
* If Docker cannot be used, it uses the existing X1 cluster to build an image.
* It can be used inside (for example, in JupyterLab) and outside an X1 cluster (for example, from user's laptop).
* It leverages the existing infrastructure to access X1 cluster and its resources.
* It supports direct K8s cluster API and X1 cluster API, when the former is not available.

## Overview

First, you need to create a builder:

```python
import x1.docker

# Create a builder for default infrastructure (usually your existing X1 cluster)
builder = x1.docker.builder()
```

Second, build an image and push it to the private Docker registry in the provided infrastructure:

```python
import x1.docker

builder = x1.docker.builder()
image = builder.build(path='docker/my-image', tag='my-image:0.0.1')
```

Note that both `path` and `tag` are currently required.

Additional arguments for `build` can be found here: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build.

Example:

```python
import x1.docker

builder = x1.docker.builder()
image = builder.build(
    path='docker/my-image',
    tag='my-image:0.0.1',
    buildargs={'http_proxy': 'http://my-proxy:8080'}
)
```

## Builder for specific infrastructure

```python
import x1
import x1.docker

# Create a builder for the remote cluster mycluster.x1infra.com
infrastructure = x1.infrastructure(address='mycluster.x1infra.com')
builder = x1.docker.builder(infrastructure=infrastructure)
```

### Specify a builder kind

By default `x1.docker.builder()` returns a builder that works with the existing infrastructure.
For example, if there is a local Docker daemon is available, then it will be used to build a Docker image locally.
This is faster than building an image in the cluster, because it requires uploading files to the cluster.

User can request a specific kind of the builder, by specifying `kind`.

Use a local builder that leverages the existing Docker daemon to build Docker images locally and push to the private registry in the cluster:

```python
import x1.docker

builder = x1.docker.builder(kind='docker')
```

Use a remote builder that leverages Prefect in remote cluster to build Docker images remotely and push to the private registry in the cluster:

```python
import x1.docker

builder = x1.docker.builder(kind='prefect')
```

### Specify Docker registry

To push an image to a custom Docker registry instead of registry in the cluster:

```python
import x1.docker

builder = x1.docker.builder(registry='https://myregistry.x1infra.com')
```

TODO: add auth for registry.

