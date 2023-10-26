import x1
import x1.base
from x1.plugins import x1_infrastructure


def test_default_infrastructure():
    infra = x1.infrastructure()
    assert isinstance(infra, x1.base.Infrastructure)
    assert infra.address == ''
    assert infra.kind == 'X1'

    infra_impl = x1.base.get_infrastructure_implementation(infra)
    assert isinstance(infra_impl, x1_infrastructure.X1InfrastructureImplementation)


def test_x1_infrastructure():
    infra = x1.infrastructure(infrastructure_type="X1")
    assert isinstance(infra, x1.base.Infrastructure)
    assert infra.address == ''
    assert infra.kind == 'X1'

    infra = x1.infrastructure(infrastructure_type="X1", address='example.com')
    assert isinstance(infra, x1.base.Infrastructure)
    assert infra.address == 'example.com'
    assert infra.kind == 'X1'
