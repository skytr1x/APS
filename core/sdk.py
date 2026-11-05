import io
import json
import os
import shutil
import stat
import tempfile
import urllib.request
import zipfile

from .constants import MAX_DOWNLOAD, MAX_FILES, MAX_UNPACKED, SDK_URL, TEMP_PREFIX
from .errors import APSError


def read_limited(stream, limit):
    data = bytearray()
    while True:
        block = stream.read(min(65536, limit + 1 - len(data)))
        if not block:
            break
        data.extend(block)
        if len(data) > limit:
            raise APSError('err_too_large')
    return bytes(data)


def extract_sdk(data, directory):
    if len(data) > MAX_DOWNLOAD:
        raise APSError('err_archive_too_large')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > MAX_UNPACKED:
            raise APSError('err_sdk_limits')
        paths = []
        for info in infos:
            name = info.filename
            parts = name.rstrip('/').split('/')
            mode = (info.external_attr >> 16) & 0xffff
            if (not name or '\\' in name or name.startswith('/') or
                any(p in ('', '.', '..') for p in parts) or
                stat.S_ISLNK(mode) or info.flag_bits & 1):
                raise APSError('err_bad_entry')
            paths.append(parts)

        # root-level or one folder deep
        names = [('/'.join(p), i) for p, i in zip(paths, infos) if not i.is_dir()]
        matches = [n for n, _ in names if n == 'aps-sdk.json' or n.endswith('/aps-sdk.json')]
        if len(matches) != 1:
            raise APSError('err_no_manifest')
        prefix = matches[0][:-len('aps-sdk.json')]
        components = prefix.rstrip('/').split('/') if prefix else []
        if len(components) > 2 or (len(components) == 2 and components[1] != 'sdk'):
            raise APSError('err_bad_layout')

        manifest = json.loads(archive.read(matches[0]).decode('utf-8'))
        if manifest.get('name') != 'aps-sdk' or manifest.get('abi') != 1:
            raise APSError('err_sdk_incompatible')
        file_names = {n[len(prefix):] for n, _ in names if n.startswith(prefix)}
        if 'Cargo.toml' not in file_names or 'src/lib.rs' not in file_names:
            raise APSError('err_sdk_incomplete')

        seen = set()
        for name, info in names:
            if not name.startswith(prefix):
                continue  # ignore files outside the sdk folder
            relative = name[len(prefix):]
            if not relative or relative in seen:
                raise APSError('err_duplicates')
            seen.add(relative)
            path = os.path.join(directory, *relative.split('/'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with archive.open(info) as src, open(path, 'xb') as dst:
                remaining = info.file_size
                while remaining:
                    chunk = src.read(min(65536, remaining))
                    if not chunk:
                        raise APSError('err_corrupt')
                    dst.write(chunk)
                    remaining -= len(chunk)
                if src.read(1):
                    raise APSError('err_bad_size')
        return manifest


def _remove_path(path):
    try:
        if os.path.islink(path) or not os.path.isdir(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)
    except FileNotFoundError:
        pass


def install_sdk(home, fetch=None, progress=lambda key: None, cancelled=lambda: False):
    os.makedirs(home, exist_ok=True)
    if cancelled():
        raise APSError('err_cancelled')
    progress('progress_installing')
    if fetch is None:
        req = urllib.request.Request(SDK_URL, headers={'User-Agent': 'APS/0.8'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = read_limited(response, MAX_DOWNLOAD)
    else:
        data = fetch()
    if cancelled():
        raise APSError('err_cancelled')

    stage = tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=home)
    try:
        manifest = extract_sdk(data, stage)
        progress('progress_finishing')
        if cancelled():
            raise APSError('err_cancelled')
        dest = os.path.join(home, 'sdk')
        backup = os.path.join(home, TEMP_PREFIX + 'previous')
        _remove_path(backup)
        if os.path.lexists(dest):
            os.replace(dest, backup)
        try:
            os.replace(stage, dest)
            stage = None
        except Exception:
            if os.path.lexists(backup) and not os.path.lexists(dest):
                os.replace(backup, dest)
            raise
        _remove_path(backup)
        return manifest
    finally:
        if stage and os.path.exists(stage):
            shutil.rmtree(stage)


def remove_sdk(home):
    target = os.path.join(home, 'sdk')
    if os.path.islink(target):
        raise APSError('err_sdk_symlink')
    removed = False
    if os.path.lexists(target):
        if not os.path.isdir(target):
            raise APSError('err_sdk_not_dir')
        trash = tempfile.mkdtemp(prefix=TEMP_PREFIX + 'removed-', dir=home)
        try:
            os.replace(target, os.path.join(trash, 'sdk'))
        except Exception:
            shutil.rmtree(trash, ignore_errors=True)
            raise
        removed = True
    _sweep_leftovers(home)
    return removed


def _sweep_leftovers(home):
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


def sdk_manifest(home):
    try:
        with open(os.path.join(home, 'sdk', 'aps-sdk.json'), encoding='utf-8') as f:
            data = json.load(f)
        if (isinstance(data, dict) and data.get('name') == 'aps-sdk' and data.get('abi') == 1 and
                os.path.isfile(os.path.join(home, 'sdk', 'Cargo.toml')) and
                os.path.isfile(os.path.join(home, 'sdk', 'src', 'lib.rs'))):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return None


def sdk_installed(home):
    return sdk_manifest(home) is not None


def sdk_state(home):
    if sdk_installed(home):
        return 'ready'
    if os.path.lexists(os.path.join(home, 'sdk')):
        return 'broken'
    return 'missing'
