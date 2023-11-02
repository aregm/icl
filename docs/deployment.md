# Deploying ICL cluster

ICL cluster is a Kubernetes cluster with additional applications deployed and configured to work together.

The simplest way to get a working ICL cluster is to use one of the available scripts:

* [scripts/deploy/kind.sh](kind.md) - creates a local single node cluster using kind (https://github.com/kubernetes-sigs/kind).
* [scripts/deploy/aws.sh](aws.md) - creates a multi node ICL cluster based on AWS EKS.
* [scripts/deploy/gke.sh](gcp.md) - creates a multi node ICL cluster based on GCP GKE.

For other scenarios,
such as deploying to the existing Kubernetes cluster, or deploying on virtual machines or bare-metal servers,  
you need a Control Node: a machine that can access Kubernetes API directly or via jump host.
That Control Node needs certain tools installed, see below.
Alternatively, you can use Containerized Control Node (CCN), which is a Docker container that contains all required tools installed.
Control Node is needed only to deploy and maintain ICL cluster.
Once ICL is deployed, Control Node can be turned off, assuming that all configuration files are permanently stored, for example, in git or local file system. 

Next steps:
* Prepare [Control Node](#control-node) or [Containerized Control Node](#containerized-control-node).
* If you already have a Kubernetes cluster, jump to [deploying ICL to Kubernetes](#deploy-icl-to-kubernetes)
* If you have bare-metal machines or virtual machines provisioned with a supported Operating System,
  you have an option to deploy a [Kubernetes cluster with Kubespray](#deploy-kubernetes).
* If you are starting from scratch, you have an option to deploy ICL to [virtual machines](#virtual-nodes),
  or [provision bare-metal machines](#bare-metal-nodes) with the supported Operating System.


## Control Node

* Install `terraform`, `kubectl`, `helm`, `git`.
* TODO.

## Containerized Control Node

* Install Docker.
* TODO.

## Bare-metal nodes

The following Operating Systems are supported for bare-metal nodes:

* Ubuntu 22.04
* Rocky Linux 9

We have Ansible playbooks and roles (TODO) that we use in our CI to provision bare-metal nodes.
You can use them as a starting point for your infrastructure.

## Virtual nodes

The following Operating Systems are supported:

* Ubuntu 22.04
* Rocky Linux 9

We have Vagrant files (TODO) and Terraform modules (TODO)  that we use in our CI to bring up Virtual Machines on libvirt.
You can use them as a starting point for your infrastructure.

## Deploy Kubernetes

We use [Kubespray](https://github.com/kubernetes-sigs/kubespray) in our CI to deploy Kubernetes to provisioned bare-metal and virtual machines.
You can use our cluster profiles and scripts as a starting point for your infrastructure.

## Deploy ICL to Kubernetes

ICL applications are installed and configured with Terraform.
The Terraform module for ICL is located in directory `terraform/icl`.
To deploy ICL to Kubernetes you need:

* Kubernetes configuration file (default location is `~/.kube/config`) with administrative permissions for the cluster.
* Environment variables `KUBECONFIG` and `KUBE_CONFIG_PATH` set to the location of Kubernetes configuration file.
* Terraform variables for ICL (usually stored in `terraform.tfvars` or `terraform.tfvars.json`).
  See examples of cluster profiles (TODO).

## Expose ICL endpoints

ICL applications can be accessed via HTTP [endpoints](endpoints.md).
If you have a local ICL cluster deployed with [kind](kind.md), then all endpoints are available in domain "localtest.me", which resolves to 127.0.0.1.
In other cases, you need to manually configure DNS zone for your cluster.
Alternatively, ICL can configure your DNS zone with external-dns (TODO).
