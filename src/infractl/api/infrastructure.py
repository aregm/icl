"""ICL infrastructure."""

import infractl.base


def default_infrastructure() -> infractl.base.Infrastructure:
    """Returns a default ICL infrastructure."""
    return infrastructure(kind='ICL')


def infrastructure(*args, kind: str = 'ICL', **kwargs) -> infractl.base.Infrastructure:
    if kind == 'ICL':
        # import required plugin
        # pylint: disable=import-outside-toplevel, unused-import
        from infractl.plugins import icl_infrastructure  # noqa

        return infractl.base.Infrastructure(*args, kind=kind, **kwargs)

    raise NotImplementedError(f'Infrastructure {kind} is not implemented')
