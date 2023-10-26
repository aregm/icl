#!/usr/bin/env python3

"""X1 hub CLI."""

# pylint: disable=unused-import
import x1.hub.config
import x1.hub.jupyterhub
import x1.hub.server
from x1.hub.root import cli

if __name__ == '__main__':
    cli()
