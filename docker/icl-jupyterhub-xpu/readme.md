ICL GPU JupyterHub image
ICL JupyterHub image with GPU tools and user-level dependencies.

Build and push the image
BASE_TAG=pbchekin/icl-jupyterhub:latest
TARGET_TAG=pbchekin/icl-jupyterhub-gpu:latest
docker build . \
    --progress=plain \
    --tag $TARGET_TAG \
    --build-arg BASE_TAG $BASE_TAG
docker push $TARGET_TAG