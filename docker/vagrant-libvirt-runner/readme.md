# GitHub runner image for Vagrant VMs

Get [gh-runner script](https://github.com/leshikus/gh-runner) and `x1` repo. The script needs a context from `x1/docker/vagrant-libvirt-runner/`.

```
git clone https://github.com/leshikus/gh-runner
git clone https://github.com/aregm/icl/
```

Set `RUNNER_NAME=icl/x1/libvirt-vagrant-1` and `TOKEN` from Github

Run the following:


```
sh gh-runner/run.sh  --token $TOKEN --context x1/docker/vagrant-libvirt-runner/ $RUNNER_NAME --labels vagrant-libvirt --become
```

Notes:

* End runner names with a number if you want to have several runners run in parallel. These numbers are used to define a separate cluster network.
* If you restart a runner, then just omit `--token $TOKEN` option, it will use cached credentials.
