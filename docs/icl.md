# ICL Quick start

## Run a Python program

To run a Python program remotely:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py'))
await program.run()
```

To specify arguments for the program:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py'))
await program.run(parameters=['--help'])
```

To specify a function to execute:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py', name='main'))
await program.run()
```

To specify a function to execute and its parameters:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py', name='main'))
await program.run(parameters={'foo': 'bar'})
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
import x1

program = await x1.deploy(x1.program('my_flow.py'))
await program.run()
```

If the Python file contains of multiple flows, it's required to choose the flow that will be deployed.
Example:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py', name='my_flow2'))
await program.run()
```

Currently, the default infrastructure is expected to be available locally and accessible via `localtest.me`, which resolves to 127.0.0.1.
See [docs/kind.md](docs/kind.md) for the instructions to install a local single node X1 cluster.

To deploy a flow to a remote X1 cluster define a custom infrastructure with an address of the remote cluster. 

```python
import x1

infrastructure = x1.infrastructure(address='mycluster.x1infra.com')
program = await x1.deploy(x1.program('my_flow.py'), infrastructure=infrastructure)
await program.run()
```

To run a flow with parameters:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py'))
await program.run(parameters={'url': 'https://example.com'})
```

Note that Prefect recommends using [pydantic models](https://docs.prefect.io/concepts/flows/#parameters) to define flow parameters.

# Infrastructure parameters

Infrastructure has the following parameters:

* `address` - an optional address of the infrastructure.
If not specified, then the default infrastructure will be used, which is expected to be available locally with address `localtest.me`, which resolves to 127.0.0.1.
See [docs/kind.md](docs/kind.md) for the instructions to install a local single node X1 cluster.

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
import x1

runtime = x1.runtime(
    environment={'foo': 'bar'},
    dependencies={'pip': ['boto', 'botocore']},
)
program = await x1.deploy(x1.program('my_flow.py'), runtime=runtime)
```

Currently, `dependencies` accepts only requirements that can be installed with `pip`.
The value for `pip` is a list of [pip requirements specifiers](https://pip.pypa.io/en/stable/reference/requirement-specifiers/).

Example:

```python
import x1

runtime = x1.runtime(
    # 'data.csv' from the local working directory will be copied to the runtime working directory 
    files=['data.csv'],
)
program = await x1.deploy(x1.program('my_flow.py'), runtime=runtime)
```

# Deployment parameters

When deploying a flow, it is possible to specify additional parameters for [Prefect Deployment](https://docs.prefect.io/2.10.21/api-ref/prefect/deployments/deployments/#prefect.deployments.deployments.Deployment).
Below are several examples of using deployment parameters for Prefect flow:

## Tag a flow

To add tags to the Prefect flow:

```python
import x1

program = await x1.deploy(x1.program('my_flow.py'), tags=['my_flow'])
```

## Schedule a flow

To specify a [schedule](https://docs.prefect.io/2.10.21/concepts/schedules/) for a flow:

```python
import x1

# This schedule will create flow runs for this deployment every day at midnight.
program = await x1.deploy(x1.program('my_flow.py'), schedule={'cron': '0 0 * * *'})
```

## Customize a Kubernetes job

To apply a [JSON patch](https://jsonpatch.com/) to the Prefect Kubernetes job:

```python
import x1

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

program = await x1.deploy(x1.program('my_flow.py'), customizations=customizations)
```

## Specify a custom flow name

There are 3 options to specify a Prefect flow name for X1 program:

1. With argument `name` in `x1.deploy()`:

   ```python
   x1.deploy(program, name='renamed')
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

## Stream logs from X1 program

 ```python
 program = await x1.deploy(
     x1.program('flows/flow7.py'),
     name='flow7-test-stream-logs',
 )
 # Run the flow without waiting for the Terminal state, use `detach=True`
 program_run = await program.run(detach=True)

 # this command will print logs to sys.stdout
 await program_run.stream_logs()

 # this command will print logs to `file`
 file = StringIO()
 await program_run.stream_logs(file=file)

 # how to read logs
 file.seek(0)
 logs = file.read()

 # It is possible to change the frequency of sending requests to receive logs via `poll_interval`.
 await program_run.stream_logs(poll_interval=60)  # 60 sec
 ```

# Docker images

[ICL build API](icl-build.md) allows building custom Docker images and pushing them to a Docker registry.

For example, to build a Docker image and push it to the private Docker registry in the provided infrastructure:

```python
import x1.docker

builder = x1.docker.builder()
image = builder.build(path='docker/my-image', tag='my-image:0.0.1')
```
