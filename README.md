# Infrastructure Control Language

Tool to easily run your data science, machine learning or deep learning experiments anywhere - local, on-prem cluster or hybrid cloud. 
Based on Infrastructure as Code, but pushed to the next level. Provides cosmic level of infrastructure control bringing old good days back when you can run program on the machine you develop.

Still in engineering Alpha mode. Use with caution. But let us know what you think!

## Description
Install
OS - Ubuntu 22.04 or later/Rocky Linux 9. 
Docker should be installed. 
Commands to deploy.

```bash
git clone https://github.com/intel-ai/icl.git
cd icl
./scripts/deploy/kind.sh
```

## What's in Package?
Out of the box ICL will provide an integrated set of data science libraries:

Pandas/Modin
Scikit-Learn
XGBoost
PyTorch/Tensorflow
Ray
MatplotLib

##Quick start
The cluster's endpoints are accessible only from localhost:

* http://dashboard.localtest.me

* http://jupyter.localtest.me

* http://minio.localtest.me

* http://prefect.localtest.me

In your browser, navigate to http://jupyter.localtest.me.

### Define a flow
Flow comprised tasks is the main unit of deployment. Currently, ICL uses Prefect for defining basic workflow building blocks: flow and tasks.

Create a Python file my_flow.py that defines a single flow my_flow:
```Python
from prefect import flow

@flow
def my_flow():
    print('Hello from my_flow')
Note this is a regular Python file, so it can be developed, tested, and executed locally.

Deploy and run a flow
The following code deploys and runs flow my_flow in the default infrastructure:

import ICL

program = await ICL.deploy('my_flow.py')
await program.run()
```
## Links
docs/kind.md
