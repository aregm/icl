import infractl
import infractl.base
from infractl.plugins import icl_infrastructure


def test_default_infrastructure():
    infra = infractl.infrastructure()
    assert isinstance(infra, infractl.base.Infrastructure)
    assert infra.address == ''
    assert infra.kind == 'ICL'

    infra_impl = infractl.base.get_infrastructure_implementation(infra)
    assert isinstance(infra_impl, icl_infrastructure.IclInfrastructureImplementation)


def test_infractl_infrastructure():
    infra = infractl.infrastructure(infrastructure_type="ICL")
    assert isinstance(infra, infractl.base.Infrastructure)
    assert infra.address == ''
    assert infra.kind == 'ICL'

    infra = infractl.infrastructure(infrastructure_type="ICL", address='example.com')
    assert isinstance(infra, infractl.base.Infrastructure)
    assert infra.address == 'example.com'
    assert infra.kind == 'ICL'
