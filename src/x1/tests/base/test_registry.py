import pytest

import x1.base


class TheClass(metaclass=x1.base.RegisteredClass):
    pass


class SubClass(TheClass):
    pass


def test_registered_class():
    instance = x1.base.RegisteredClass.get(TheClass, 'SubClass')()
    print(instance.__class__)
    assert isinstance(instance, SubClass)
    with pytest.raises(KeyError):
        _ = x1.base.RegisteredClass.get(TheClass, 'NoSuchClass')
