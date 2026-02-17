# Container-based control node

This is the basic container to deploy and manage ICL nodes.
It contains the minimal set of management tools:

* Python
* Kubespray
* Kubectl
* Helm
* Terraform

## How to build

```aiignore
TARGET_TAG = pbchekin/icl-ccn:latest
docker build . --progress=plain --tag $TARGET_TAG
docker push $TARGET_TAG 
```
