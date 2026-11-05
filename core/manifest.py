import json
import os

from .constants import ABI_VERSION, HOST_VERSION, MANIFEST, REQUIRED_FILES, SDK_NAME


def sdk_dir(home):
    return os.path.join(home, 'sdk')


def _read(home):
    try:
        with open(os.path.join(sdk_dir(home), MANIFEST), encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError, TypeError):
        return None
    if isinstance(data, dict) and data.get('name') == SDK_NAME and data.get('abi') == ABI_VERSION:
        return data
    return None


def sdk_state(home):
    root = sdk_dir(home)
    if not os.path.lexists(root):
        return 'missing'
    data = _read(home)
    if data is None:
        return 'broken'
    if data.get('host') != HOST_VERSION:
        return 'outdated'
    complete = all(os.path.isfile(os.path.join(root, *name.split('/'))) for name in REQUIRED_FILES)
    return 'ready' if complete else 'broken'


def sdk_manifest(home):
    return _read(home) if sdk_state(home) == 'ready' else None
