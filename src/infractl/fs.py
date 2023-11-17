"""File system functions."""

import pathlib
import sys
import tarfile
import urllib.parse
from typing import List

import infractl.base


def strip_file_scheme(uri: str) -> str:
    """Strips "file" scheme from the URI.

    Examples:
        file:///C:/Windows -> C:/Windows
        file:///home -> /home
        file:local -> local
    """
    path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
    if sys.platform == 'win32' and path.startswith('/'):
        # workaround to remove leading slash on Windows
        return path[1:]
    return path


def prepare_to_upload(files: List[infractl.base.RuntimeFile], target_path: pathlib.Path):
    """Uploads files to the specified directory."""
    # The specified directory has the following structure:
    # cwd.tar  - tarball to extract to the current directory in runtime.
    with tarfile.open(name=target_path / 'cwd.tar', mode='w') as cwd:
        for file in files:
            if file.src.endswith('/'):
                src = pathlib.Path(file.src)
                dst = ''
                if file.dst:
                    # dst is expected to be a directory, adding a trailing / if missing
                    dst = file.dst if file.dst.endswith('/') else f'{file.dst}/'
                for path in src.rglob('*'):
                    relative_path = path.relative_to(src)
                    cwd.add(name=path, arcname=f'{dst}{relative_path}')
            else:
                dst = file.dst or file.src
                cwd.add(name=file.src, arcname=pathlib.Path(dst).name)
