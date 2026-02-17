#!/bin/bash

set -e

conda_prefix=$HOME/.conda
jupyterlab_env="base"
kernel_env="python-3.12"

# Fix the owner and permissions for /home/jovyan
# TODO: check if passwordless sudo is enabled
sudo chown jovyan:jovyan /home/jovyan
sudo chmod 00700 /home/jovyan

cd ~

if [[ ! -d $conda_prefix ]]; then
  echo "$conda_prefix does not exists, copying from /template"
  tar xf /template/conda.tar.xz
fi

if [[ ! -f ~/.profile ]]; then
  echo "No .profile in $HOME, creating one"
  echo "source $conda_prefix/etc/profile.d/conda.sh" >> ~/.profile
  echo "conda activate python-3.12" >> ~/.profile
  if [[ -f /opt/intel/oneapi/setvars.sh ]]; then
    echo "source /opt/intel/oneapi/setvars.sh || true" >> ~/.profile
  fi
fi

if [[ ! -f ~/.jupyter/jupyter_config.json ]]; then
  echo "no .jupyter/jupyter_config.json in $HOME, creating one"
  mkdir -p ~/.jupyter
  # Use kernel display_name, filter out a kernel from jupyterlab environment
  cat <<EOF > ~/.jupyter/jupyter_config.json
{
  "CondaKernelSpecManager": {
    "conda_only": true,
    "name_format": "{display_name}"
  }
}
EOF

  # Use environment name for display_name
  kernel_json=$conda_prefix/envs/$kernel_env/share/jupyter/kernels/python3/kernel.json
  jq ".display_name = \"$kernel_env\"" $kernel_json > /tmp/kernel.json
  mv /tmp/kernel.json $kernel_json
  unset kernel_json
fi

source $conda_prefix/etc/profile.d/conda.sh
conda activate $jupyterlab_env

unset conda_prefix
unset jupyterlab_env
unset kernel_env

# Remove default kernel
jupyter kernelspec remove -y python3 || true

# Remove lost+found
rm -rf lost+found

exec jupyterhub-singleuser