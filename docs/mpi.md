# MPI in X1

## CPU

Create `tensorflow-benchmarks.yaml` with the following content:

```yaml
apiVersion: kubeflow.org/v2beta1
kind: MPIJob
metadata:
  name: tensorflow-benchmarks
spec:
  slotsPerWorker: 1
  runPolicy:
    cleanPodPolicy: Running
  mpiReplicaSpecs:
    Launcher:
      replicas: 1
      template:
         spec:
           containers:
           - image: mpioperator/tensorflow-benchmarks:latest
             name: tensorflow-benchmarks
             command:
             - mpirun
             - --allow-run-as-root
             - -np
             - "2"
             - -bind-to
             - none
             - -map-by
             - socket
             - -x
             - NCCL_DEBUG=INFO
             - -x
             - LD_LIBRARY_PATH
             - -x
             - PATH
             - -mca
             - pml
             - ob1
             - -mca
             - btl
             - ^openib
             - python
             - scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py
             - --model=resnet101
             - --batch_size=32
             - --device=cpu
             - --data_format=NHWC
             - --variable_update=horovod
    Worker:
      replicas: 2
      template:
        spec:
          containers:
          - image: mpioperator/tensorflow-benchmarks:0.3.0
            name: tensorflow-benchmarks
            
            # This is required only for OpenShift to allow workers to do chroot,
            securityContext:
              privileged: true
          
          # Anti affinity rule to make sure workers are scheduled to different nodes.  
          affinity:
            podAntiAffinity:
              preferredDuringSchedulingIgnoredDuringExecution:
                - weight: 1
                  podAffinityTerm:
                    labelSelector:
                      matchExpressions:
                        - key: training.kubeflow.org/job-role
                          operator: In
                          values:
                            - worker
                    topologyKey: kubernetes.io/hostname
```

```shell
kubectl apply -f tensorflow-benchmarks.yaml
```

Check that launcher and worker pods are running:

```shell
kubectl get pods -l training.kubeflow.org/job-name=tensorflow-benchmarks
```

Show launcher logs:

```shell
kubectl logs \
  -l training.kubeflow.org/job-name=tensorflow-benchmarks \
  -l training.kubeflow.org/job-role=launcher
```

## Links

* https://github.com/kubeflow/mpi-operator/tree/master/examples/v2beta1/tensorflow-benchmarks/
* https://github.com/tensorflow/benchmarks/blob/master/scripts/tf_cnn_benchmarks/