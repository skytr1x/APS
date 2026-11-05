import importlib
import importlib.util
import os
import sys

from .constants import HOST_DIR, HOST_PACKAGE
from .errors import APSError


def unload_host():
    for name in [n for n in sys.modules if n == HOST_PACKAGE or n.startswith(HOST_PACKAGE + '.')]:
        del sys.modules[name]


def load_host(sdk_root):
    package = os.path.join(sdk_root, HOST_DIR, HOST_PACKAGE)
    unload_host()
    importlib.invalidate_caches()
    spec = importlib.util.spec_from_file_location(
        HOST_PACKAGE, os.path.join(package, '__init__.py'), submodule_search_locations=[package])
    if spec is None or spec.loader is None:
        raise APSError('err_host_load')
    module = importlib.util.module_from_spec(spec)
    sys.modules[HOST_PACKAGE] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        unload_host()
        raise APSError('err_host_load') from exc
    return module


def check_host(sdk_root, scratch):
    keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # stage must stay clean
    try:
        module = load_host(sdk_root)
        module.check_engine(scratch)
    finally:
        sys.dont_write_bytecode = keep
        unload_host()
