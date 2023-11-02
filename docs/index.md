# Infrastructure Control Language

## What is ICL?


Infrastructure Control Language (ICL) is designed to run programs anywhere: locally or in distributed on-premises or cloud environments.

ICL consists of:

* Python library `infractl` that allows to execute programs in ICL clusters.
* ICL cluster that is a Kubernetes cluster with pre-configured open-source applications.
* Instructions, scripts, infrastructure as code (IaC) blueprints that allow deploying ICL clusters in different environments, such as containers, existing Kubernetes clusters, virtual and bare-metal machines, clouds.  

`infractl` allows executing the same code in different ICL clusters with different runtime configurations.
Currently, it requires at least one ICL cluster, but in the future it will work directly with public clouds, virtual machines, bare-metal servers. 
The simplest way to start using `infractl` is to create a local single node ICL cluster in a Docker container. 

ICL is designed for data scientists, solo developers and small teams who are transitioning from a local development to a distributed, shared environment.
How ICL helps you or your team:

* Provides the same familiar tools, such as Jupyter, VS Code, Ray, but without infra/ops burden.
* Allows executing distributed workloads that require more memory or compute that any individual workstation can provide.
* Supports shared assets such as data sets, private libraries, pre-configured environments with required dependencies.
* Provides shared compute infrastructure with controlled concurrency: a modern mainframe. 
* Enables collaborative work on shared workflows, pipelines. 
* Helps to focus on development instead of deployment, configuration, infrastructure.

## Next

* [Deploying ICL cluster](deployment.md)
  * [ICL cluster in a container](kind.md)
  * [ICL cluster in AWS](aws.md)
  * [ICL cluster in GCP](gcp.md)
  * [ICL in the existing Kubernetes cluster](deployment.md#deploy-icl-to-kubernetes)
  * [ICL cluster on virtual machines](deployment.md#virtual-nodes)
  * [ICL cluster on bare-metal machines](deployment.md#bare-metal-nodes)
* [infractl](infractl.md)
  * [infractl infrastructure](infractl.md#infrastructure-parameters)
  * [infractl runtime](infractl.md#runtime-parameters)
  * [infractl runtime files](infractl-runtime-files.md)
  * [infractl build](infractl-build.md)
* ICL
  * [ICL cluster endpoints](endpoints.md)
  * [SSH access to JupyterHub session](jupyterhub-ssh.md)
