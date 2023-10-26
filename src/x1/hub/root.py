"""Root group for X1 hub commands.

The click group `cli` is the root group and entry point for all x1 hub commands.
"""

import click


@click.group()
def cli():
    """X1 hub CLI."""
