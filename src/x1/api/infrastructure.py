"""X1 infrastructure Facade."""

import x1.base


def default_infrastructure() -> x1.base.Infrastructure:
    """Returns a default X1 infrastructure."""
    return infrastructure(kind='X1')


def infrastructure(*args, kind: str = 'X1', **kwargs) -> x1.base.Infrastructure:
    if kind == 'X1':
        # import required plugin
        # pylint: disable=import-outside-toplevel, unused-import
        from x1.plugins import x1_infrastructure  # noqa

        return x1.base.Infrastructure(*args, kind=kind, **kwargs)

    raise NotImplementedError(f'Infrastructure {kind} is not implemented')
