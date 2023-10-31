"""icl-hub server."""

from infractl.hub import root


@root.cli.group()
def server():
    """Manage icl-hub server."""


@server.command()
def start():
    """Start icl-hub server."""
    # pylint: disable=import-outside-toplevel
    import uvicorn

    uvicorn.run('infractl.hub.rest:app', host='0.0.0.0', port=8000, reload=False)
