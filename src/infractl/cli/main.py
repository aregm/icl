#!/usr/bin/env python3

"""ICL CLI."""

import logging
import os
import urllib.parse
from typing import Optional

import click
import requests

import infractl.base


@click.group()
def main():
    """ICL CLI tool."""
    logging.basicConfig(level=logging.INFO)


@main.group()
def ssh():
    """Manage SSH access to JupyterHub session."""
    if 'JUPYTERHUB_USER' not in os.environ:
        raise click.ClickException(
            'Environment variable JUPYTERHUB_USER not set, are you in JupyterHub session?'
        )


@ssh.command('enable')
@click.option('--key', help='Public SSH key')
def enable_ssh_cmd(key: Optional[str] = None):
    """Enable ssh to JupyterHub session."""
    print('Enabling SSH access ...')
    print(
        'Use the following command to log in to your session:',
        enable_ssh(os.getenv('JUPYTERHUB_USER'), key),
    )


@ssh.command('disable')
def disable_ssh_cmd():
    """Disable ssh to JupyterHub session."""
    print('Disabling SSH access ...')
    print(disable_ssh(os.getenv('JUPYTERHUB_USER')))


def get_hub_url() -> str:
    """Returns icl-hub address."""
    # TODO: support HTTP and HTTPS schemas, move to upper level
    return infractl.base.SETTINGS.get(
        'hub_url',
        f'http://hub.{infractl.base.SETTINGS.get("default_address", "localtest.me")}',
    )


def enable_ssh(username: str, key: Optional[str] = None) -> str:
    """Enable ssh to JupyterHub session.

    Returns:
        ssh connection string
    """
    url = f'{get_hub_url()}/jupyterhub/ssh/enable/{urllib.parse.quote(username)}'
    response = requests.post(url, json={'key': key}, timeout=300)
    response.raise_for_status()
    return str(response.json())


def disable_ssh(username: str) -> str:
    """Disable ssh to JupyterHub session."""
    url = f'{get_hub_url()}/jupyterhub/ssh/disable/{urllib.parse.quote(username)}'
    response = requests.post(url, timeout=60)
    response.raise_for_status()
    return str(response.json())


if __name__ == '__main__':
    main()
