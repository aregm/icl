# infractl quick start

## Import infractl

```python
import infractl
```

## Run a Python program

To run a Python program remotely:

```python
await infractl.run(infractl.program('my_flow.py'))
```

To specify arguments for the program:

```python
await infractl.run(infractl.program('my_flow.py'), parameters=['--help'])
```

To specify a function to execute:

```python
await infractl.run(infractl.program('my_flow.py', name='main'))
```

To specify a function to execute and its parameters:

```python
await infractl.run(infractl.program('my_flow.py', name='main'), parameters={'foo': 'bar'})
```

## Run a flow

Currently, ICL uses [Prefect](https://docs.prefect.io/) for defining basic workflow building blocks: [flow and tasks](https://docs.prefect.io/tutorials/first-steps/#flows-tasks-and-subflows).

Create a Python file `my_flow.py` that defines a single flow `my_flow`: 

```python
from prefect import flow

@flow
def my_flow():
    print('Hello from my_flow')
```

Note this is a regular Python file, so it can be developed, tested, and executed locally.
The following code deploys and runs flow `my_flow` in the default infrastructure:

```python
await infractl.run(infractl.program('my_flow.py'))
```

If the Python file contains of multiple flows, it's required to choose the flow that will be deployed.
Example:

```python
await infractl.run(infractl.program('my_flow.py', name='my_flow'))
```

Currently, the default infrastructure is expected to be available locally and accessible via `localtest.me`, which resolves to 127.0.0.1.

To deploy a flow to a remote ICL cluster define a custom infrastructure with an address of the remote cluster. 

```python
infrastructure = infractl.infrastructure(address='mycluster.example.com')
await infractl.deploy(infractl.program('my_flow.py'), infrastructure=infrastructure)
```

To run a flow with parameters:

```python
await infractl.deploy(infractl.program('my_flow.py'), parameters={'url': 'https://example.com'})
```

Note that Prefect recommends using [pydantic models](https://docs.prefect.io/concepts/flows/#parameters) to define flow parameters.

# Infrastructure parameters

Infrastructure has the following parameters:

* `address` - an optional address of the infrastructure.
If not specified, then the default infrastructure will be used, which is expected to be available locally with address `localtest.me`, which resolves to 127.0.0.1.
See the [instructions](kind.md) to install a local single node ICL cluster.

* `gpus` - an optional request for GPUs in the infrastructure.
If not specified, then no GPUs will be available.
If specified as a number, then the specified number of any GPUs will be available.
If specified as a tuple, for example, `('gpu.intel.com/i915', 1)`, then the specified number of requested GPUs will be available. 

# Runtime parameters

Runtime has the following parameters:

* `environment` - environment variables to set in the runtime.

* `dependencies` - Python dependencies to install in the runtime.

* `files` - files that must be present in the runtime, see [runtime files](icl-runtime-files.md). 

Example:

```python
runtime = infractl.runtime(
    environment={'foo': 'bar'},
    dependencies={'pip': ['boto', 'botocore']},
)
infractl.run(infractl.program('my_flow.py'), runtime=runtime)
```

Currently, `dependencies` accepts only requirements that can be installed with `pip`.
The value for `pip` is a list of [pip requirements specifiers](https://pip.pypa.io/en/stable/reference/requirement-specifiers/).

Example:

```python
runtime = infractl.runtime(
    # 'data.csv' from the local working directory will be copied to the runtime working directory 
    files=['data.csv'],
)
await infractl.run(infractl.program('my_flow.py'), runtime=runtime)
```

# Deployment parameters

When deploying a flow, it is possible to specify additional parameters for [Prefect Deployment](https://docs.prefect.io/2.10.21/api-ref/prefect/deployments/deployments/#prefect.deployments.deployments.Deployment).
Below are several examples of using deployment parameters for Prefect flow:

## Tag a flow

To add tags to the Prefect flow:

```python
infractl.run(infractl.program('my_flow.py'), tags=['my_flow'])
```

## Schedule a flow

To specify a [schedule](https://docs.prefect.io/2.10.21/concepts/schedules/) for a flow:

```python
# This schedule will create flow runs for this deployment every day at midnight.
await infractl.run(infractl.program('my_flow.py'), schedule={'cron': '0 0 * * *'})
```

## Customize a Kubernetes job

To apply a [JSON patch](https://jsonpatch.com/) to the Prefect Kubernetes job:

```python
# This customization adds a second container `busybox` to the pod.
# Make sure to terminate the second container when the main container completes!
customizations = [
    {
        'op': 'add',
        'path': '/spec/template/spec/containers/1',
        'value': {
            'name': 'busybox',
            'image': 'busybox',
            'cmd': ['/bin/echo', 'hello from busybox'],
        },
    },
]
await infractl.run(infractl.program('my_flow.py'), customizations=customizations)
```

## Specify a custom flow name

There are 3 options to specify a Prefect flow name for the program:

1. With argument `name` in `infractl.deploy()`:

   ```python
   infractl.run(program, name='renamed')
   ```

2. With argument `name` in `flow` decorator:

   ```python
   @flow(name='renamed')
   def my_flow():
     ...
   ```

3. If both arguments are not specified, then Prefect will derive a flow name from a function name.
   For example, function `my_flow` will be deployed as flow `my-flow`. 

# Program run parameters

* `parameters` - a dictionary of named arguments if program's entrypoint is a function,
  otherwise - a list of arguments. 

* `timeout` - timeout in seconds for waiting for the program to complete,
  `None` to wait forever (default).

* `detach` - `False` to wait for the program completion (default), `True` - do not wait for program completion.

## Stream logs from the program

 ```python
# Run the flow without waiting for the Terminal state, use `detach=True`
program = await infractl.run(
    infractl.program('flows/flow7.py'),
    detach=True,
)

# this command will print logs to sys.stdout
await program.stream_logs()

# this command will print logs to `file`
file = StringIO()
await program.stream_logs(file=file)

# how to read logs
file.seek(0)
logs = file.read()

# It is possible to change the frequency of sending requests to receive logs via `poll_interval`.
await program.stream_logs(poll_interval=60)  # 60 sec
```

# Docker images

[infractl build API](infractl-build.md) allows building custom Docker images and pushing them to a Docker registry.
For example, to build a Docker image and push it to the private Docker registry in the provided infrastructure:

```python
import infractl.docker

builder = infractl.docker.builder()
image = builder.build(path='docker/my-image', tag='my-image:0.0.1')
```
