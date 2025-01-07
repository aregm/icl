Based on icl-ccn image.

Build
```
BASE_TAG=pbchekin/icl-ccn:latest
TARGET_TAG=pbchekin/icl-ccn-kubespray:latest
docker build . \
    --progress=plain \
    --tag $TARGET_TAG \
    --build-arg BASE_TAG=$BASE_TAG
docker push $TARGET_TAG
```