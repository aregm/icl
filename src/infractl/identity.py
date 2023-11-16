"""Methods to generate and sanitize identities (names)."""

import os
import platform
import re
from typing import Optional


def sanitize(identity: str) -> str:
    """Sanitizes the value to make it compatible with Kubernetes/Prefect names.

    * must be 1 to 63 characters
    * must begin and end with an alphanumeric character
    * could contain dashes (-) and alphanumerics between
    """
    # replace non-alphanumeric characters with '-'
    identity = re.sub('[^0-9a-zA-Z]+', '-', identity.lower())
    # replace repeating '-' with a single one, strip heading and leading '-'
    return re.sub('--+', '-', identity).strip('-')


def generate(prefix: Optional[str] = None, suffix: Optional[str] = None) -> str:
    """Generates stable identity for the current user.

    Uses environment variables `JUPYTERHUB_USER`, `USER` and sanitizes the value to make it
    compatible with Prefect names.
    """
    identity = (
        os.environ.get('JUPYTERHUB_USER') or os.environ.get('USER') or platform.node() or 'unknown'
    )
    prefix = f'{prefix}-' if prefix else ''
    suffix = f'-{suffix}' if suffix else ''
    return sanitize(prefix + identity + suffix)
