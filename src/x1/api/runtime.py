"""X1 runtime Facade."""

import x1.base


def default_runtime() -> x1.base.Runtime:
    """Returns a default program runtime."""
    return x1.base.Runtime(kind='prefect')


def runtime(*args, kind: str = 'prefect', **kwargs) -> x1.base.Runtime:
    if kind == 'prefect':
        # pylint: disable=import-outside-toplevel, unused-import, redefined-outer-name
        import x1.plugins.prefect_runtime.runtime  # noqa

        return x1.base.Runtime(*args, kind=kind, **kwargs)

    raise NotImplementedError(f'Runtime {kind} is not implemented')
