# GitHub runner image for Vagrant VMs

Get [gh-runner script](https://github.com/leshikus/gh-runner) and `x1` repo. The script needs a context from `x1/docker/vagrant-libvirt-runner/`.

```
git clone https://github.com/leshikus/gh-runner
git clone https://github.com/intel-sandbox/x1
```

Set `RUNNER_NAME=intel-sandbox/x1/libvirt-vagrant-1` and `TOKEN` from Github

Run the following:


```
export no_proxy=intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,127.0.0.0/8,134.134.0.0/16,172.16.0.0/16,localtest.me,apt.repos.intel.com,x1infra.com
export http_proxy=http://proxy-us.intel.com:912
export https_proxy=http://proxy-us.intel.com:912

sh gh-runner/run.sh  --token $TOKEN --context x1/docker/vagrant-libvirt-runner/ $RUNNER_NAME --labels vagrant-libvirt --become
```

Notes:

* End runner names with a number if you want to have several runners run in parallel. These numbers are used to define a separate cluster network.
* If you restart a runner, then just omit `--token $TOKEN` option, it will use cached credentials.
