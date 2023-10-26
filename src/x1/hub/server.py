"""X1 hub server."""

from x1.hub import root


@root.cli.group()
def server():
    """Manage X1 hub server."""


@server.command()
def start():
    """Start X1 hub server."""
    # pylint: disable=import-outside-toplevel
    import uvicorn

    uvicorn.run('x1.hub.rest:app', host='0.0.0.0', port=8000, reload=False)
