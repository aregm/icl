"""ICL settings."""

import dynaconf

SETTINGS = dynaconf.Dynaconf(
    envvar_prefix='X1',  # export envvars with `export X1_FOO=bar`
    settings_files=['/etc/x1/settings.yaml', '.x1/settings.yaml'],
    merge_enabled=True,
)
