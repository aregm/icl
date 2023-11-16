"""ICL runtime."""

import infractl.base


def default_runtime() -> infractl.base.Runtime:
    """Returns a default program runtime."""
    return runtime(kind='prefect')


def runtime(*args, kind: str = 'prefect', **kwargs) -> infractl.base.Runtime:
    if kind == 'prefect':
        # pylint: disable=import-outside-toplevel, unused-import, redefined-outer-name
        import infractl.plugins.prefect_runtime.runtime  # noqa

        return infractl.base.Runtime(*args, kind=kind, **kwargs)

    if kind == 'kubernetes':
        # pylint: disable=import-outside-toplevel, unused-import, redefined-outer-name
        import infractl.plugins.kubernetes_runtime.runtime  # noqa

        return infractl.base.Runtime(*args, kind=kind, **kwargs)

    raise NotImplementedError(f'Runtime {kind} is not implemented')
