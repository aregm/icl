import os
from unittest import mock

import pytest

import x1
import x1.docker
import x1.docker.remote

Image = x1.docker.Image


def test_image_from_full_name():
    assert Image.from_full_name(full_name='ubuntu') == Image(name='ubuntu')
    assert Image.from_full_name(full_name='ubuntu:22.04') == Image(name='ubuntu', tag='22.04')
    assert Image.from_full_name(full_name='docker.io/ubuntu') == Image(
        registry='docker.io', name='ubuntu'
    )
    assert Image.from_full_name(full_name='docker.io/ubuntu:22.04') == Image(
        registry='docker.io', name='ubuntu', tag='22.04'
    )
    assert Image.from_full_name(full_name='localhost:5000/ubuntu') == Image(
        registry='localhost:5000', name='ubuntu'
    )
    assert Image.from_full_name(full_name='localhost:5000/ubuntu:22.04') == Image(
        registry='localhost:5000', name='ubuntu', tag='22.04'
    )


def test_image_full_name():
    def assert_full_name(full_name: str):
        assert Image.from_full_name(full_name=full_name).full_name == full_name

    assert_full_name('ubuntu')
    assert_full_name('ubuntu:22.04')
    assert_full_name('docker.io/ubuntu')
    assert_full_name('docker.io/ubuntu:22.04')
    assert_full_name('localhost:5000/ubuntu')
    assert_full_name('localhost:5000/ubuntu:22.04')
    assert Image(id='id').full_name == 'id'


def test_registry_endpoint():

    builder = x1.docker.builder(registry='localhost:5000')
    assert builder.registry_endpoint == 'https://localhost:5000'

    builder = x1.docker.builder(registry='http://localhost:5000')
    assert builder.registry_endpoint == 'http://localhost:5000'


@mock.patch.dict(os.environ, {'KUBERNETES_SERVICE_HOST': ''}, clear=True)
def test_registry_endpoint_internal():
    builder = x1.docker.builder(infrastructure=x1.infrastructure(address='nosuchhost.no'))
    assert (
        builder.registry_endpoint == 'http://docker-registry.docker-registry.svc.cluster.local:5000'
    )


@mock.patch.dict(os.environ, {}, clear=True)
def test_registry_endpoint_external():
    builder = x1.docker.builder(infrastructure=x1.infrastructure(address='nosuchhost.no'))
    assert builder.registry_endpoint == 'http://registry.nosuchhost.no'


def test_builder_kind():
    builder = x1.docker.builder(
        infrastructure=x1.infrastructure(),
        kind='prefect',
    )
    assert isinstance(builder, x1.docker.remote.Builder)


def test_unsupported_builder_kind():
    with pytest.raises(NotImplementedError):
        _ = x1.docker.builder(
            infrastructure=x1.infrastructure(),
            kind=x1.docker.BuilderKind.KUBERNETES,
        )
    with pytest.raises(NotImplementedError):
        _ = x1.docker.builder(
            infrastructure=x1.infrastructure(),
            kind='no_such_kind',
        )
