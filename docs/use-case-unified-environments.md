# Unification of environments

## Types of environments

For a software project, historically there are several types of environments: 

* development
* testing
* staging
* production

These environments can be very different.
For example, staging and production environments can have controlled access, bigger scale, monitoring and logging, security.
However, there are still common characteristics in terms of dependencies and configuration.

## CI environments

For CI (Continuous Integration) there are CI environments, which has special characteristics such as reproducibility, isolation, and consistency.
In essence, however, CI environments have a lot of common with development and testing environments.
It is required a lot of efforts and special build tools to make a build process consistent in development and CI environments, since it is important to have the same result in both environments.
For some projects, reproducible builds are a crucial aspect of software security and quality assurance.
By ensuring that the build process is deterministic and transparent, organizations can enhance trust, improve security, and streamline their software development workflows.

## Configuration drift

Usually the responsibility of maintaining such environments is spread across different roles or teams.
It is not uncommon to see a configuration drift, when one environment is updated with a new dependency, but it is still not propagated to other environments.
In worst cases, the gap between environments can be so big that teams, for example, have to maintain completely different configuration for testing, staging, and production environments.
Such drifts open a Pandora's box of all kind of problems and require a lot of efforts to fix. 

## Unifying common characteristics of environments 

Ideally, all common characteristics of all environments must be defined as code, so any change to such configuration is versioned and automatically propagated to environments.
Configuration specific for environment, for example, staging, production needs to be defined with the same terms, and can be translated to familiar target, such as Terraform.
Such approach should minimize configuration drift.
When implemented right, at least several environments, such as development, testing, and CI can be unified.
With proper isolation and consistency, an idling development environment can be used by CI/CD orchestrator to run a workflow, or manually executed tests can be promoted as a successful CI run.
There is no need in dedicated compute pool for CI, because all available compute resources can be used for CI runs and developments sessions.

## Similarities with platform engineering

A history of platform engineering efforts shows that development and devops teams need high level building blocks to implement their own platform.
The existing building blocks, such as Terraform, Kubernetes, Cloud APIs now are considered as low-level, and teams spend a considerable amount of time on infrastructure needs.
