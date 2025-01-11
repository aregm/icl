# Deploying ICL cluster to GCP

## Prerequisites

* Docker 
* GCP project is specified:

    ```shell
    export X1_GCP_PROJECT_NAME="my-project-name"
    ```
* GCP region is specified:

    ```shell
    export X1_GCP_ZONE="us-central1-b"
    ```

* Credentials to access a GCP account (user or service account).
    * To use user account, skip this step: this will be handled later
    * To use service account:

        ```shell
        export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"
        ```

## Deploy ICL cluster

```shell
./scripts/deploy/gke.sh
```

* `~/.config/gcloud` will be mounted inside
* If using user account, you'll be asked to grant access using a browser session (if not yet done)

## Delete ICL cluster

```shell
./scripts/deploy/gke.sh --delete
```

## Advanced scenarios

### Control node console

The following command starts an ephemeral control node in a Docker container and starts a new Bash session:   

```shell
./scripts/deploy/gke.sh --console
```

The Kubernetes context is configured in that control node,
so you can use `kubectl`, `helm` and so on in that Bash session. 

### HTTP and HTTPS proxies

The script uses the following environment variables if they are set:

* `http_proxy`
* `https_proxy`
* `no_proxy`

Note that the proxy is only used by the script itself, it is not used in the cluster.

### Tests

```shell
./scripts/deploy/gke.sh --console

# On control node execute
export ICL_INGRESS_DOMAIN={ingress_domain}
./scripts/ccn/test.sh
```
