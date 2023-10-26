import dynaconf

import x1
import x1.base
import x1.docker.remote


def test_manifest_filter():
    settings = dynaconf.Dynaconf()
    settings.update(
        {
            'localtest.me': {
                'registry_internal_endpoint': 'http://internal.endpoint',
            }
        }
    )
    x1.base.SETTINGS = settings
    builder = x1.docker.remote.Builder(infrastructure=x1.infrastructure(address='localtest.me'))
    manifest = builder.manifest_filter(
        {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
            'metadata': {'labels': {}},
            'spec': {
                'template': {
                    'spec': {
                        'parallelism': 1,
                        'completions': 1,
                        'restartPolicy': 'Never',
                        'containers': [
                            {
                                'name': 'prefect-job',
                                'env': [],
                            }
                        ],
                    }
                }
            },
        }
    )

    job = manifest['spec']
    pod = job['template']['spec']

    assert len(pod['containers']) == 2, 'pod has 2 containers'

    prefect_container = pod['containers'][0]
    dind_container = pod['containers'][1]

    assert prefect_container['name'] == 'prefect-job'
    assert dind_container['name'] == 'dind'
    print(manifest)
