"""Root group for icl-hub commands.

The click group `cli` is the root group and entry point for all icl-hub commands.
"""

import click


@click.group()
def cli():
    """icl-hub CLI."""
