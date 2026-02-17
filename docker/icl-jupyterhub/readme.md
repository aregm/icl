ICL JupyterHub image
Overview
conda-based
passwordless sudo, potentially can be disabled later
additional packages installed (gh cli, ssh, vim, rsync, s3cmd)
Modin, Prefect, Ray, ICL
Build and push the image
TARGET_TAG=pbchekin/icl-jupyterhub:latest
MODIN_VERSION="0.26.1"
PREFECT_VERSION="2.13.0"
RAY_VERSION="2.9.2"
Needs to be run from the root of the repository:

docker build . \
    --file docker/icl-jupyterhub/Dockerfile \
    --progress=plain \
    --tag $TARGET_TAG \
    --build-arg PREFECT_VERSION="$PREFECT_VERSION" \
    --build-arg MODIN_VERSION="$MODIN_VERSION" \
    --build-arg RAY_VERSION="$RAY_VERSION"    
docker push $TARGET_TAG
Create custom JupyterLab kernel
In Terminal, create a new conda environment and install ipykernel.

conda_env="my-env"

conda create --name $conda_env python=3.12 ipykernel
Optionally, change the display name for the kernel.

display_name="My Env"

kernel_json=$HOME/.conda/envs/$conda_env/share/jupyter/kernels/python3/kernel.json
jq ".display_name = \"$display_name\"" $kernel_json > /tmp/kernel.json
mv /tmp/kernel.json $kernel_json
Restarting JupyterLab is not required, however the new display name will be applied with a delay.