# OpenVINO in ICL cluster

## Model Server with a single model

### Jupyter

```shell
# Install OpenVINO Development Tools
pip install openvino-dev

# Download resnet-50-tf model and convert it to OpenVINO IR format
omz_downloader --name resnet-50-tf
omz_converter --name resnet-50-tf
```

```shell
# Make sure s3cmd >= 2.3.0 is installed.
# Create configuration for s3cmd,
cat <<EOF >>~/.s3cfg
host_base = minio.minio
host_bucket = minio.minio
bucket_location = us-east-1
use_https = True
check_ssl_certificate = False

# Setup access keys
access_key = x1miniouser
secret_key = x1miniopass

# Enable S3 v4 signature APIs
signature_v2 = False
EOF
```

Upload model to the model repository in S3 bucket.
This requires `~/.s3cfg` from the above.
The [model repository] in S3 needs to have a specific directory structure.

```shell
# Create bucket `models` if does not exist
s3cmd mb s3://models

# The model contains two subdirectories: `FP16` and `FP32`
s3cmd sync public/resnet-50-tf/FP32/ s3://models/resnet-50-tf/1/
```

The final directory structure should look like: 

```
s3://models/resnet-50-tf/1/resnet-50-tf.bin
s3://models/resnet-50-tf/1/resnet-50-tf.mapping
s3://models/resnet-50-tf/1/resnet-50-tf.xml
```

### Control node

```shell
# Create a new OVMS instance
cat <<EOF | kubectl --namespace default create -f -
apiVersion: intel.com/v1alpha1
kind: ModelServer
metadata:
  name: resnet-50-tf
spec:
  image_name: openvino/model_server:latest
  models_settings:
    model_name: resnet-50-tf
    model_path: s3://models/resnet-50-tf
  server_settings:
    file_system_poll_wait_seconds: 0
    sequence_cleaner_poll_wait_minutes: 0
    log_level: INFO
  models_repository:
    storage_type: S3
    aws_region: us-east-1
    aws_access_key_id: x1miniouser
    aws_secret_access_key: x1miniopass
    s3_compat_api_endpoint: http://s3.icx.x1infra.com
EOF
```

See [Model server parameters] and [Model server Helm chart parameters] for more details.

Check that the OVMS pod is running:

```shell
$ kubectl --namespace default get pods -l release=resnet-50-tf
NAME                                READY   STATUS    RESTARTS   AGE
resnet-50-tf-ovms-dfb6d6b68-5xnc4   1/1     Running   0          13m
```

Check that OVMS service exists:

```shell
kubectl --namespace default get services -l release=resnet-50-tf
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
resnet-50-tf-ovms   ClusterIP   192.168.78.30   <none>        8080/TCP,8081/TCP   14m
```

The OVMS instance has the following internal endpoints, accessible within the cluster:

* `resnet-50-tf-ovms.default:8080` (GRPC endpoint)
* `resnet-50-tf-ovms.default:8081` (REST endpoint)

### Jupyter

Check that the REST endpoint is accessible:

```shell
curl -sS http://resnet-50-tf-ovms.default:8081/v1/config | jq .
{
  "resnet-50-tf": {
    "model_version_status": [
      {
        "version": "1",
        "state": "AVAILABLE",
        "status": {
          "error_code": "OK",
          "error_message": "OK"
        }
      }
    ]
  }
}
```

Use `ovmsclient` to check that the endpoint works:

```shell
git clone https://github.com/openvinotoolkit/model_server
cd model_server/client/python/ovmsclient/samples
pip install -r requirements.txt

MODEL_ENDPOINT=resnet-50-tf-ovms.default:8080

python grpc_predict_binary_resnet.py \
  --images_dir ../../../../demos/common/static/images/ \
  --service_url $MODEL_ENDPOINT \
  --model_name resnet-50-tf
```

Example output:

```
Image ../../../../demos/common/static/images/zebra.jpeg has been classified as zebra
Image ../../../../demos/common/static/images/arctic-fox.jpeg has been classified as Arctic fox, white fox, Alopex lagopus
Image ../../../../demos/common/static/images/peacock.jpeg has been classified as peacock
Image ../../../../demos/common/static/images/golden_retriever.jpeg has been classified as golden retriever
Image ../../../../demos/common/static/images/pelican.jpeg has been classified as pelican
Image ../../../../demos/common/static/images/bee.jpeg has been classified as bee
Image ../../../../demos/common/static/images/snail.jpeg has been classified as snail
Image ../../../../demos/common/static/images/gorilla.jpeg has been classified as gorilla, Gorilla gorilla
Image ../../../../demos/common/static/images/magnetic_compass.jpeg has been classified as magnetic compass
Image ../../../../demos/common/static/images/airliner.jpeg has been classified as warplane, military plane
```

## See also

* [OpenVINO Quickstart Guide]

[OpenVINO Quickstart Guide]: https://docs.openvino.ai/2022.2/ovms_docs_quick_start_guide.html
[Model repository]: https://docs.openvino.ai/latest/ovms_docs_models_repository.html
[Model server parameters]: https://github.com/openvinotoolkit/operator/blob/main/docs/modelserver_params.md
[Model server Helm chart parameters]: https://github.com/openvinotoolkit/operator/blob/main/helm-charts/ovms/values.yaml