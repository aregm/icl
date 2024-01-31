"""Infrastructure for ICL cluster."""

import functools
from typing import Optional

import dynaconf

import infractl.base
from infractl.plugins.ssh.utils import ZymeClient


class SshInfrastructureImplementation(
    infractl.base.InfrastructureImplementation,
    registration_name='ssh',
):
    """SSH Infrastructure specification."""

    # Custom settings to use instead of global infractl.base.SETTINGS
    _settings: Optional[dynaconf.Dynaconf] = None

    @functools.cached_property
    def address(self) -> str:
        """Gets infrastructure address."""
        target = self.infrastructure
        if target.address:
            return target.address
        current_settings = self._settings or infractl.base.SETTINGS
        return current_settings.get('default_address', 'localtest.me')

    def get_client(self) -> ZymeClient:
        return ZymeClient(
            hostname=self.infrastructure.address,
            username=self.infrastructure.username,
            password=self.infrastructure.password,
            port=self.infrastructure.port,
        )
