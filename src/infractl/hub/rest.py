"""icl-hub REST API."""
from typing import Optional

import fastapi
import pydantic

from infractl.hub import config, jupyterhub

app = fastapi.FastAPI()


class JupyterHubEnableSshRequest(pydantic.BaseModel):
    """Request to enable SSH for JupyterHub session."""

    key: Optional[str] = pydantic.Field(
        title='SSH public key',
        default=None,
    )


@app.get('/healthz')
def get_health():
    """Health check."""
    return 'OK'


@app.get('/config')
def get_config_values():
    """Configuration values."""
    return config.get_dict()


@app.get('/config/{key}')
def get_config_value(key: str):
    """Configuration value."""
    return config.get().get(key)


@app.get('/jupyterhub/users')
def get_jupyterhub_users():
    """JupyterHub users."""
    return jupyterhub.list_users()


@app.post('/jupyterhub/ssh/enable/{user}')
def jupyterhub_ssh_enable(user: str, body: JupyterHubEnableSshRequest):
    """Enable SSH for JupyterHub session."""
    print(user, body.key)
    return jupyterhub.enable_ssh(user, body.key)


@app.post('/jupyterhub/ssh/disable/{user}')
def jupyterhub_ssh_disable(user: str):
    """Disable SSH for JupyterHub session."""
    jupyterhub.disable_ssh(user)
    return 'OK'
