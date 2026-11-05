import io
import json
import os
import stat
import zipfile

from .constants import (ABI_VERSION, HOST_VERSION, MANIFEST, MAX_DOWNLOAD, MAX_FILES,
                        MAX_UNPACKED, REQUIRED_FILES, SDK_NAME)
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


def _entry_parts(info):
    name = info.filename
    parts = name.rstrip('/').split('/')
    mode = (info.external_attr >> 16) & 0xffff
    if (not name or '\\' in name or name.startswith('/') or
            any(p in ('', '.', '..') for p in parts) or
            stat.S_ISLNK(mode) or info.flag_bits & 1):
        raise APSError('err_bad_entry')
    return parts


def _find_prefix(names):
    matches = [n for n in names if n == MANIFEST or n.endswith('/' + MANIFEST)]
    if len(matches) != 1:
        raise APSError('err_no_manifest')
    prefix = matches[0][:-len(MANIFEST)]
    parts = prefix.rstrip('/').split('/') if prefix else []
    if len(parts) > 2 or (len(parts) == 2 and parts[1] != 'sdk'):
        raise APSError('err_bad_layout')
    return matches[0], prefix


def _write_entry(archive, info, path):
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


def extract_sdk(data, directory):
    if len(data) > MAX_DOWNLOAD:
        raise APSError('err_archive_too_large')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > MAX_UNPACKED:
            raise APSError('err_sdk_limits')
        parts = [_entry_parts(info) for info in infos]
        files = [('/'.join(p), i) for p, i in zip(parts, infos) if not i.is_dir()]
        manifest_name, prefix = _find_prefix([n for n, _ in files])

        manifest = json.loads(archive.read(manifest_name).decode('utf-8'))
        if (manifest.get('name') != SDK_NAME or manifest.get('abi') != ABI_VERSION
                or manifest.get('host') != HOST_VERSION):
            raise APSError('err_sdk_incompatible')
        present = {n[len(prefix):] for n, _ in files if n.startswith(prefix)}
        if not all(name in present for name in REQUIRED_FILES):
            raise APSError('err_sdk_incomplete')

        seen = set()
        for name, info in files:
            if not name.startswith(prefix):
                continue  # outside the sdk folder
            relative = name[len(prefix):]
            if not relative or relative in seen:
                raise APSError('err_duplicates')
            seen.add(relative)
            _write_entry(archive, info, os.path.join(directory, *relative.split('/')))
        return manifest
