#!/bin/sh

clean_all() {
  ps -ef
  echo "Cleaning vagrant"
  vagrant destroy -f || true

  echo "Cleaning domains"
  virsh list --all
  virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh destroy || true
  virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh undefine || true

  echo "Cleaning nets"
  virsh net-list --all
  virsh net-destroy "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true
  virsh net-undefine "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true

  echo "Cleanup finished"
}

generate_key() {
  test -f ~/.ssh/id_rsa || ssh-keygen -q -b 2048 -t rsa -N '' -C 'cluster key' -f ~/.ssh/id_rsa
  mkdir -p generated
  ln -snf ~/.ssh/id_rsa generated/
  ln -snf ~/.ssh/id_rsa.pub generated/
}

ensure_vagrant_plugins() {
  if ! vagrant plugin list | grep -q vagrant-proxyconf; then
    vagrant plugin install vagrant-proxyconf
  fi
  if ! vagrant plugin list | grep -q vagrant-reload; then
    vagrant plugin install vagrant-reload
  fi
  if ! vagrant plugin list | grep -q vagrant-scp; then
    vagrant plugin install vagrant-scp
  fi
}

ensure_vagrant_plugins
clean_all
generate_key
