import pathlib

from infractl.base import runtime


def test_runtime_dependencies():
    deps = runtime.RuntimeDependencies(pip=['infractl'])
    assert deps.pip == ['infractl'], 'pip is set correctly'


def test_runtime_dependencies_from_dict():
    deps = runtime.parse_dependencies(
        {
            'pip': ['infractl'],
        }
    )
    assert deps.pip == ['infractl'], 'pip is set correctly'


def test_runtime_dependencies_from_empty_dict():
    deps = runtime.parse_dependencies({})
    assert deps.pip == [], 'pip is set correctly'


def test_none_runtime_files():
    files = runtime.parse_files(None)
    assert files == []


def test_empty_runtime_files():
    files = runtime.parse_files([])
    assert files == []


def test_runtime_files():
    files = runtime.parse_files(
        [
            'src1',
            runtime.RuntimeFile(src='src2'),
            runtime.RuntimeFile(src='src3', dst='dst3'),
            {'src': 'src4'},
            {'src': 'src5', 'dst': 'dst5'},
            pathlib.Path('src'),
            {'src': pathlib.Path('src')},
            {'src': pathlib.Path('src'), 'dst': 'dst'},
            {'src': pathlib.Path('src'), 'dst': pathlib.Path('dst')},
        ]
    )
    assert files == [
        runtime.RuntimeFile(src='src1'),
        runtime.RuntimeFile(src='src2'),
        runtime.RuntimeFile(src='src3', dst='dst3'),
        runtime.RuntimeFile(src='src4'),
        runtime.RuntimeFile(src='src5', dst='dst5'),
        runtime.RuntimeFile(src='src'),
        runtime.RuntimeFile(src='src'),
        runtime.RuntimeFile(src='src', dst='dst'),
        runtime.RuntimeFile(src='src', dst='dst'),
    ]
