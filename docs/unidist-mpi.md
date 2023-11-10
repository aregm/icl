# Run unidist with MPI backend from source for NY-taxi benchmark

This uses the [docker container](/docker/unidist-mpi/Dockerfile) built with unidist mpi backend.

# CPU

Create `unidist-mpi.yaml` with the following content:

In the YAML file the directory `/data` has been mounted on launher and worker pods.

**Note:** As in the below example, the value of `UNIDIST_CPUS` would be 2 less than number of mpi ranks. 0 rank is for master process and 1 rank is for monitor process. Other ranks are for workers.

The YAML file below launches 8 worker pods (replicas: 8) on which modin with unidist-mpi backend is run.
As the "-n" flag of mpexec is set to 16, each worker pod will have 2 mpi ranks running.
The first worker pod will have unidist master and monitor processes, all the remaining worker pods will have 2 unidist workers per pod.

```yaml
apiVersion: kubeflow.org/v2beta1
kind: MPIJob
metadata:
  name: modin-on-unidist-mpi
spec:
  slotsPerWorker: 1
  runPolicy:
    cleanPodPolicy: Running
  mpiReplicaSpecs:
    Launcher:
      replicas: 1
      template:
         spec:
           volumes:
            - name: datadir
              persistentVolumeClaim:
               claimName: shared-volume
           containers:           
           - image: localhost:5000/modin_unidist_mpi:latest
             name: modin-unidist-ompi
             command:               
             - /usr/share/miniconda/envs/modin_on_unidist/bin/mpiexec
             - --allow-run-as-root
             - -bind-to
             - none
             - -map-by
             - socket
             - -n
             - "16"
             - --oversubscribe
             - -x
             - UNIDIST_MPI_SPAWN=False
             - -x
             - UNIDIST_MPI_LOG=True
             - -x
             - UNIDIST_CPUS=6
             - -x
             - MODIN_CPUS=6
             - /usr/share/miniconda/envs/modin_on_unidist/bin/python
             - timedf/scripts/benchmark_run.py
             - ny_taxi
             - -data_file
             - /data/benchmark-datasets/ny_taxi
             - -pandas_mode
             - Modin_on_unidist_mpi
             - -verbosity
             - "1"
             - -no_ml
             volumeMounts:
              - name: datadir
                mountPath: /data
    Worker:
      replicas: 8
      template:
        spec:
          volumes:
            - name: datadir
              persistentVolumeClaim:
               claimName: shared-volume
          containers:
          - image: localhost:5000/modin_unidist_mpi:latest
            name: modin-unidist-ompi
            volumeMounts:
              - name: datadir
                mountPath: /data
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
kubectl apply -f unidist-mpi.yaml
```

Check that launcher and worker pods are running:

```shell
kubectl get pods -l training.kubeflow.org/job-name=modin-on-unidist-mpi
```

Show launcher logs:

```shell
kubectl logs -l training.kubeflow.org/job-name=modin-on-unidist-mpi
```

