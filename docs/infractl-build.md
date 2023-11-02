# Build

infractl build API allows building custom Docker images and pushing them to a Docker registry.

The main features of the API:

* It leverages the existing local Docker, if exists.
* If Docker cannot be used, it uses the existing ICL cluster to build an image.
* It can be used inside (for example, in JupyterLab) and outside an ICL cluster (for example, from user's laptop).
* It leverages the existing infrastructure to access ICL cluster and its resources.
* It supports direct K8s cluster API and CIL cluster API, when the former is not available.

## Overview

First, you need to import `infractl.docker`:

```python
import infractl.docker
```

Create a builder:

```python
# Create a builder for default infrastructure (usually your existing ICL cluster)
builder = infractl.docker.builder()
```

Build an image and push it to the private Docker registry in the provided infrastructure:

```python
image = builder.build(path='docker/my-image', tag='my-image:0.0.1')
```

Note that both `path` and `tag` are currently required.

Additional arguments for `build` can be found here: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build.

Example:

```python
builder = infractl.docker.builder()
image = builder.build(
    path='docker/my-image',
    tag='my-image:0.0.1',
    buildargs={'http_proxy': 'http://my-proxy:8080'}
)
```

## Builder for specific infrastructure

```python
# Create a builder for the remote cluster mycluster.example.com
infrastructure = infractl.infrastructure(address='mycluster.example.com')
builder = infractl.docker.builder(infrastructure=infrastructure)
```

### Specify a builder kind

By default `infractl.docker.builder()` returns a builder that works with the existing infrastructure.
For example, if there is a local Docker daemon is available, then it will be used to build a Docker image locally.
This is faster than building an image in the cluster, because it requires uploading files to the cluster.

User can request a specific kind of the builder, by specifying `kind`.

Use a local builder that leverages the existing Docker daemon to build Docker images locally and push to the private registry in the cluster:

```python
builder = infractl.docker.builder(kind='docker')
```

Use a remote builder that leverages Prefect in remote cluster to build Docker images remotely and push to the private registry in the cluster:

```python
builder = infractl.docker.builder(kind='prefect')
```

### Specify Docker registry

To push an image to a custom Docker registry instead of registry in the cluster:

```python
builder = infractl.docker.builder(registry='https://myregistry.example.com')
```
