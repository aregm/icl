import pydantic

from infractl.base.runtime import RuntimeFile
from infractl.plugins.kubernetes_runtime import engine


class Foo(pydantic.BaseModel):
    foo: str


def test_get_full_name():
    assert engine.get_full_name(RuntimeFile) == 'infractl.base.runtime.RuntimeFile'


def test_from_full_name():
    obj = engine.from_full_name('infractl.base.runtime.RuntimeFile')()
    assert obj.__class__.__name__ == 'RuntimeFile'


def test_dumps_loads():
    data = engine.loads(engine.dumps(['arg1', 'arg2']))
    assert data == ['arg1', 'arg2']

    data = engine.loads(engine.dumps({'foo': 'bar'}))
    assert data == {'foo': 'bar'}

    data = engine.loads(engine.dumps(Foo(foo='bar')))
    assert data == Foo(foo='bar')

    data = engine.loads(engine.dumps(42))
    assert data == 42
