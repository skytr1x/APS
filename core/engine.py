import os
import threading

from .constants import ID_RE
from .errors import APSError
from .plugins import plugin_path
from .sdk import sdk_installed


class WasmModule:
    def __init__(self, path):
        try:
            import aps_wasm
        except ImportError as exc:
            raise APSError('err_engine_missing') from exc
        self.engine = aps_wasm.core.Runtime()
        self.module = self.engine.instance_from_file(path, {})

    def has(self, name):
        return any(export.name == name for export in self.module.exps)

    def exec(self, name, args):
        result = self.engine.invocate(self.module, name, args)
        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        return result


class Runtime:
    # no time or memory limits
    def __init__(self, home, loader=None):
        self.home = home
        self.modules = {}
        self.lock = threading.RLock()
        self.loader = loader

    def start(self, plugin_id):
        if not ID_RE.fullmatch(plugin_id):
            raise APSError('err_bad_plugin_id')
        loader = self.loader if self.loader is not None else WasmModule
        with self.lock:
            if not sdk_installed(self.home):
                raise APSError('err_sdk_missing')
            if plugin_id in self.modules:
                return
            path = plugin_path(self.home, plugin_id)
            if os.path.islink(path) or not os.path.isfile(path):
                raise APSError('err_plugin_file_missing')
            instance = loader(path)
            if instance.exec('aps_abi_version', []) != 1:
                raise APSError('err_abi')
            if instance.exec('aps_on_load', []) != 0:
                raise APSError('err_load_failed')
            self.modules[plugin_id] = instance

    def stop(self, plugin_id):
        with self.lock:
            instance = self.modules.pop(plugin_id, None)
            if instance is not None:
                instance.exec('aps_on_unload', [])

    def close(self):
        for plugin_id in list(self.modules):
            try:
                self.stop(plugin_id)
            except Exception:
                pass

    def app_event(self, event):
        with self.lock:
            for instance in list(self.modules.values()):
                if not instance.has('aps_on_app_event'):
                    continue
                try:
                    instance.exec('aps_on_app_event', [int(event)])
                except Exception:
                    pass

    def send(self, account):
        with self.lock:
            for instance in list(self.modules.values()):
                if not instance.has('aps_on_send_message'):
                    continue
                result = instance.exec('aps_on_send_message', [int(account)])
                if result == 1:
                    return 1
                if result != 0:
                    raise APSError('err_unknown_hook')
        return 0
