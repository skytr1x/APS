import os

from .constants import ID_RE, MAX_WASM, PLUGIN_EXT
from .errors import APSError
from .sdk import read_limited


def plugin_path(home, plugin_id):
    return os.path.join(home, 'plugins', plugin_id + PLUGIN_EXT)


def plugin_ids(home):
    folder = os.path.join(home, 'plugins')
    if not os.path.isdir(folder):
        return []
    suffix_len = len(PLUGIN_EXT)
    return sorted(n[:-suffix_len] for n in os.listdir(folder)
                  if n.endswith(PLUGIN_EXT) and ID_RE.fullmatch(n[:-suffix_len])
                  and not os.path.islink(os.path.join(folder, n))
                  and os.path.isfile(os.path.join(folder, n)))


def import_wasm(source, home):
    name = os.path.basename(source)
    if not name.endswith(PLUGIN_EXT) or not ID_RE.fullmatch(name[:-len(PLUGIN_EXT)]):
        raise APSError('err_bad_name')
    with open(source, 'rb') as src:
        data = read_limited(src, MAX_WASM)
    if not data.startswith(b'\0asm\x01\0\0\0'):
        raise APSError('err_not_wasm')

    folder = os.path.join(home, 'plugins')
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, name)
    if os.path.exists(dest):
        raise APSError('err_exists')
    with open(dest, 'xb') as out:  # don't overwrite an existing plugin
        out.write(data)
    return name[:-len(PLUGIN_EXT)]
