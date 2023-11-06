This folder contains vagrant script that creates a set of VMs that can
be used for quick development because they are initially created with
Ubuntu image and don't use MAAS for installation and configuration.

To use http proxy you need to install vagrant plugin
`vagrant-proxyconf`!

**IMPORTANT!!** If you are using http(s) proxy, make sure that cluster
subnet is included into `no_proxy` environment variable. It is
essential for `kubectl` and `helm` commands, so ansible playbooks will
fail if `no_proxy` is not set correctly.

Installation happens in two stages. First stage configures VMs
`jumphost` and `cluster-###`. Inventory file with cluster IP addresses
is generated on `jumphost`. On second stage you should login to
`jumphost` and run `./everything.sh` script in the root of vagrant
user home directory. You can also run separate playbooks listed in
this file.

For additional customization of the kubernetes cluster you can specify
a path to kubespray settings file in a variable
`X1_K8S_EXTRA_SETTINGS_FILE`. If this variable is defined, this
settings file is placed on the `jumphost` together with inventory as
`group_vars/all.yaml`.
