import os
import shutil
import tempfile
import urllib.request

from .archive import extract_sdk, read_limited
from .constants import MAX_DOWNLOAD, SDK_URL, TEMP_PREFIX
from .errors import APSError
from .manifest import sdk_dir


def _remove_path(path):
    try:
        if os.path.islink(path) or not os.path.isdir(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)
    except FileNotFoundError:
        pass


def _download(fetch):
    if fetch is not None:
        return fetch()
    req = urllib.request.Request(SDK_URL, headers={'User-Agent': 'APS/0.9'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return read_limited(response, MAX_DOWNLOAD)


def _swap(home, stage):
    dest = sdk_dir(home)
    backup = os.path.join(home, TEMP_PREFIX + 'previous')
    _remove_path(backup)
    if os.path.lexists(dest):
        os.replace(dest, backup)
    try:
        os.replace(stage, dest)
    except Exception:
        if os.path.lexists(backup) and not os.path.lexists(dest):
            os.replace(backup, dest)
        raise
    _remove_path(backup)


def install_sdk(home, fetch=None, progress=lambda key: None, cancelled=lambda: False,
                verify=lambda stage: None):
    os.makedirs(home, exist_ok=True)
    if cancelled():
        raise APSError('err_cancelled')
    progress('progress_installing')
    data = _download(fetch)
    if cancelled():
        raise APSError('err_cancelled')

    stage = tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=home)
    try:
        manifest = extract_sdk(data, stage)
        verify(stage)
        progress('progress_finishing')
        if cancelled():
            raise APSError('err_cancelled')
        _swap(home, stage)
        stage = None
        return manifest
    finally:
        if stage and os.path.exists(stage):
            shutil.rmtree(stage, ignore_errors=True)


def remove_sdk(home):
    target = sdk_dir(home)
    if os.path.islink(target):
        raise APSError('err_sdk_symlink')
    removed = False
    if os.path.lexists(target):
        if not os.path.isdir(target):
            raise APSError('err_sdk_not_dir')
        trash = tempfile.mkdtemp(prefix=TEMP_PREFIX + 'removed-', dir=home)
        try:
            os.replace(target, os.path.join(trash, 'sdk'))  # atomic rename first
        except Exception:
            shutil.rmtree(trash, ignore_errors=True)
            raise
        removed = True
    _sweep(home)
    return removed


def _sweep(home):
    try:
        entries = os.listdir(home)
    except OSError:
        return
    for entry in entries:
        if entry.startswith(TEMP_PREFIX):
            try:
                _remove_path(os.path.join(home, entry))
            except OSError:
                pass
