import pytest

import infractl.base


class TheClass(metaclass=infractl.base.RegisteredClass):
    pass


class SubClass(TheClass):
    pass


def test_registered_class():
    instance = infractl.base.RegisteredClass.get(TheClass, 'SubClass')()
    print(instance.__class__)
    assert isinstance(instance, SubClass)
    with pytest.raises(KeyError):
        _ = infractl.base.RegisteredClass.get(TheClass, 'NoSuchClass')
