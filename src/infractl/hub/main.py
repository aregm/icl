#!/usr/bin/env python3

"""icl-hub CLI."""

# pylint: disable=unused-import
import infractl.hub.config
import infractl.hub.jupyterhub
import infractl.hub.server
from infractl.hub.root import cli

if __name__ == '__main__':
    cli()
