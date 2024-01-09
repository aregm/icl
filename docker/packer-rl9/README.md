# GitHub runner for Rocky Linux image bundling

Get repos:

```
git clone https://github.com/leshikus/gh-runner
git clone https://github.com/intel-ai/icl
```

Set `TOKEN` from Github. Export `no_proxy`, `http_proxy`, `https_proxy` if needed. Run

```
sh gh-runner/run.sh --context icl/docker/packer-rl9 --device /dev/kvm --device /dev/fuse --token $TOKEN --labels packer intel-ai/icl/packer-1
```

Notes:

* End runner names with a number if you want to have several runners run in parallel. These numbers are used to define a separate cluster network.
* If you restart a runner, then just omit `--token $TOKEN` option, it will use cached credentials.

