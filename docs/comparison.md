# Comparison With Similar Systems

### Ansible

Pros:
* Configuration management
* Fast deployment
* Excellent documentation

Cons:
*Red hat
*Windows support
*Package manager

### Chef

### Terraform
+Cloud providers
+Open source
+Infrastructure as code
-Learning curve
-Version control
-Major upgrades

### AWS CloudFormation

### Puppet

### VmWare Aria Automation

### Azure Resource Manager

### Google Deployment Manager

### Spacelift

### Drone

### Scalr

### Env0

### Gluware

### Oak9

### Quali Torque

### Autocloud

### Crossplane

### Intential

### Pulumi

### Firefly

### fog.io

### libcloud

### Apache Brooklyn

### Tosca

## Sorted by popularity (google trends):
* Terraform - https://www.terraform.io/
    * https://github.com/hashicorp/terraform-cdk/tree/main - bindings on python, go, typescript and others languages. Can be useful for implementing internal logic
        * https://www.hashicorp.com/resources/cdk-for-terraform-with-python-and-its-operational-experience-at-shopstyle
        * https://www.hashicorp.com/blog/cdk-for-terraform-enabling-python-and-typescript-support
    * https://developer.hashicorp.com/terraform/cdktf/concepts/cdktf-architecture - architecture
    * https://developer.hashicorp.com/terraform/cdktf/concepts/cdktf-architecture - concepts
    * Examples:
        * https://developer.hashicorp.com/terraform/tutorials/cdktf/cdktf-build?variants=cdk-language%3Apython#define-your-cdk-for-terraform-application
    * Main entities: App, Stack, Resource
    * Maybe it also interesting/possible reuse Provider' constructor parameters (subset of):
        * https://github.com/cdktf/cdktf-provider-aws/blob/main/docs/provider.python.md - aws provider
        * https://github.com/cdktf/cdktf-provider-google/blob/main/docs/provider.python.md - gcp provider
        * https://github.com/cdktf/cdktf-provider-docker/blob/main/docs/provider.python.md - docker provider
    * Too much details
    * Comparisons:
        * https://blog.gruntwork.io/why-we-use-terraform-and-not-chef-puppet-ansible-saltstack-or-cloudformation-7989dad2865c
* Ansible - https://www.ansible.com/
    * https://docs.ansible.com/ansible/latest/network/getting_started/basic_concepts.html - concepts, hard to say is it interesting for us or not.
    * https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html - python SDK only for internal use.
    * Concepts - playbooks, written in yaml
* Chef - https://www.chef.io/
    * https://docs.chef.io/automate/architectural_overview/ - master-client architecture
    * Concepts - cookbooks, written in Ruby DSL
    * Comparisons:
        * https://www.simplilearn.com/ansible-vs-chef-differences-article
* Puppet - https://www.puppet.com/
    * https://www.puppet.com/docs/puppet/8/architecture.html - agent-server architecture
    * Concepts - manifests, written in Puppet's declarative language or a Ruby DSL


* AWS CloudFormation - https://aws.amazon.com/cloudformation/
    * "CDKTF shares core concepts and components with the Amazon Web Services Cloud Development Kit (AWS CDK), a tool that allows you to use familiar programming languages to define infrastructure on AWS CloudFormation.". Cloud provider specific.
    * https://aws.amazon.com/sdk-for-python/ - python SDK (boto3).
* Crossplane - https://www.crossplane.io/
    * https://docs.crossplane.io/v1.12/concepts/ - concepts based on Kubernetes CRDs, looks too far from what we want.
    * Comparisons:
        * https://blog.crossplane.io/crossplane-vs-terraform/
        * https://blog.brainboard.co/crossplane-vs-terraform-choosing-the-best-iac-solution-for-your-needs-56689bf6f790
* Pulumi - https://www.pulumi.com/
    * https://www.pulumi.com/docs/concepts/ - concepts
    * https://www.pulumi.com/docs/reference/pkg/python/pulumi/ - python SDK
    * Comparisons:
        * https://www.pulumi.com/docs/concepts/vs/ - compare to terraform/kubernetes/cloud SDKs/ansible
* Firefly - https://www.gofirefly.io/
    * Built on top of Terraform, Pulumi and AWS CloudFormation https://firefly-5.gitbook.io/firefly-product-docs123/appendix/support-matrix#iac-technologies
    * No documentation for concepts/architecture. Proprietary solution.

* Azure Resource Manager - https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/overview
    * https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/considerations/fundamental-concepts - concepts
    * https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/overview#consistent-management-layer - architecture
    * https://github.com/Azure/azure-sdk-for-python - python sdk
        * https://azure.github.io/azure-sdk/python_design.html - Python API Design Guidelines
    * https://learn.microsoft.com/en-us/azure/developer/python/sdk/examples/azure-sdk-example-virtual-machines?tabs=cmd#3-write-code-to-create-a-virtual-machine - example of creating a virtual machine (very difficult at first glance)
    * Cloud provider specific
* Spacelift - https://spacelift.io/
    * https://docs.spacelift.io/vendors/terraform/ Built on top of Terraform, Pulumi, AWS CloudFormation, Kubernetes, Ansible
    * https://docs.spacelift.io/concepts/stack/ Same Stack concept as in Pulumi and AWS CloudFormation and some more
    * Comparisons:
        * https://medium.com/@bitterwinsome/3-cloudops-companies-that-want-you-to-destroy-kubernetes-in-prod-f1feed6bcaed
* Scalr - https://www.scalr.com/
    * https://docs.scalr.io/docs/introduction#why-use-scalr maybe interesting
    * Platform on top of Terraform. Proprietary solution.
* Oak9 - https://oak9.io/
    * Integrates into existing flows and evaluates security
* Gluware - https://gluware.com/
* Fog.io - https://fog.io/
* Autocloud - https://www.autocloud.io/
* Env0 - https://www.env0.com/
* Intential - https://www.itential.com/
* Google Deployment Manager - https://cloud.google.com/deployment-manager/docs
    * https://github.com/googleapis/google-cloud-python Python SDK
* VmWare Aria Automation - https://www.vmware.com/products/aria-automation.html
    * VMware Cloud Agnostic Template - "Use a single cloud template to deploy on VMware Cloud or any major public cloud (AWS, Azure, Google Cloud and more) with Infrastructure as Code." !!!
    * Cloud Agnostic resources: Machine, Load Balancer, Network, Security Group, Volume. It should be noted that there is also Cloud vendor resources.
        * https://docs.vmware.com/en/vRealize-Automation/8.11/Using-and-Managing-Cloud-Assembly/GUID-1EE72CCE-A871-4E63-88E5-30C12246BBBF.html#GUID-1EE72CCE-A871-4E63-88E5-30C12246BBBF
    * Proprietary solution.
* Apache LibCloud - https://libcloud.apache.org/
    * Main resources: Compute, Storage, Load Balancers, DNS, Container. It might be useful to look at the relationships between objects and their interfaces.
    * Dead open source. Do we have anyone from apache to ask about the reasons?
* Quali Torque - https://www.quali.com/torque/
    * Control plane working with Terraform, CloudFormation, Helm, Kubernetes.
    * Proprietary solution.
    * Interesting features:
        * Tag based cost report.
        * Blueprints. For ICL it can be like a predefined description of the infrastructure and runtime, which can be accessed by file name when deploying programs. It is worth considering two views, a high-level one - python scripts, and an internal view into which ICL will translate the python code before deployment (potentially one-to-one corresponding to the resources of the provider).
