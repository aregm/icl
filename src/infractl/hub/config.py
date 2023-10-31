"""icl-hub configuration."""

import pathlib
import tempfile
from typing import Any, Dict, Optional

import dynaconf
import dynaconf.loaders

from infractl.hub import root

_CONFIG: Optional[dynaconf.Dynaconf] = None


@root.cli.group()
def config():
    """Manage ICL hub configuration."""


@config.command()
def view():
    """View configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = str(pathlib.Path(temp_dir) / 'hub.toml')
        dynaconf.loaders.write(config_path, get_dict())
        with open(config_path, mode='r', encoding='utf-8') as config_file:
            print(config_file.read())


def get() -> dynaconf.Dynaconf:
    """Gets configuration."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = dynaconf.Dynaconf(
            envvar_prefix='X1',
            # override by SETTINGS_FILE_FOR_DYNACONF or SETTINGS_FILES_FOR_DYNACONF
            preload=['.x1/hub.toml'],
            merge_enabled=True,
        )
    return _CONFIG


def get_dict() -> Dict[str, Any]:
    """Gets configuration as dictionary.

    Used to return all configuration keys and values.
    """
    # Make top level keys lower case since dynaconf makes them uppercase by default
    return {key.lower(): value for key, value in get().as_dict().items()}
