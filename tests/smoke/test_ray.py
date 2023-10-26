import time
from os import getenv

import ray
from pytest import mark


def ray_init(address, retries=10, retry_delay=30):
    last_error = None
    for retry in range(1, retries):
        try:
            ray.init(address=address)
            return
        except ConnectionError as error:
            last_error = error
            print(f'Received {error}, retrying {retry}/{retries} in {retry_delay}s ...')
            time.sleep(retry_delay)
            continue
    if last_error:
        raise last_error


@ray.remote
def f(x):
    return x * x


@mark.skipif(
    getenv("DISABLE_RAY_TEST") != None, reason="Ray test is disabled by setting DISABLE_RAY_TEST"
)
def test_ray(ray_endpoint):
    ray_init(address=f'ray://{ray_endpoint}')
    living_nodes = [node for node in ray.nodes() if node.get('alive')]
    print(f'Using Ray cluster with {len(living_nodes)} nodes')

    futures = [f.remote(i) for i in range(4)]
    assert ray.get(futures) == [0, 1, 4, 9]
