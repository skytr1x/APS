from .errors import APSError
from .install import install_sdk, remove_sdk
from .loader import check_host, load_host, unload_host
from .manifest import sdk_dir, sdk_manifest, sdk_state
from .release import release_version


class PluginService:
    def __init__(self, home, get_setting, set_setting, logger=None):
        self.home = home
        self.get_setting = get_setting
        self.set_setting = set_setting
        self.logger = logger
        self.host = None

    # sdk
    def state(self):
        state = sdk_state(self.home)
        if state == 'ready' and self.host is None:
            return 'broken'  # files are fine, host failed to import
        return state

    def installed(self):
        return self.state() == 'ready'

    def manifest(self):
        return sdk_manifest(self.home) if self.installed() else None

    def latest_release(self):
        return release_version()

    def load(self):
        self.unload()
        if sdk_state(self.home) != 'ready':
            return False
        try:
            module = load_host(sdk_dir(self.home))
            self.host = module.Host(self.home, self.get_setting, self.set_setting, self.logger)
        except Exception:
            self.host = None
            if self.logger:
                self.logger.exception('APS: failed to load the sdk host')
            return False
        self.host.start_enabled()
        return True

    def unload(self):
        host, self.host = self.host, None
        if host is not None:
            host.close()
        unload_host()

    def install(self, progress=lambda key: None, cancelled=lambda: False, fetch=None):
        self.unload()
        try:
            install_sdk(self.home, fetch=fetch, progress=progress, cancelled=cancelled,
                        verify=lambda stage: check_host(stage, self.home))
        finally:
            loaded = self.load()  # new sdk, or the old one if install failed
        if not loaded:
            raise APSError('err_host_load')

    def remove(self):
        self.unload()
        remove_sdk(self.home)

    def close(self):
        self.unload()

    # plugins
    def need_host(self):
        host = self.host
        if host is None:
            raise APSError('err_sdk_missing')
        return host

    def ids(self):
        host = self.host
        return host.ids() if host else []

    def metadata(self, plugin_id):
        host = self.host
        reader = getattr(host, 'metadata', None) if host else None
        if reader is None:
            return None
        try:
            return reader(plugin_id)
        except Exception:
            if self.logger:
                self.logger.exception('APS: failed to read metadata for %s', plugin_id)
            return None

    def enabled(self, plugin_id):
        host = self.host
        return bool(host and host.enabled(plugin_id))

    def set_enabled(self, plugin_id, enabled):
        host = self.host
        if host:
            host.set_enabled(plugin_id, enabled)

    def enabled_ids(self):
        host = self.host
        return host.enabled_ids() if host else []

    def disable_all(self):
        host = self.host
        if host:
            host.disable_all()

    def toggle(self, plugin_id, enabled):
        self.need_host().toggle(plugin_id, enabled)

    def import_plugin(self, source):
        return self.need_host().import_plugin(source)

    def remove_plugin(self, plugin_id):
        self.need_host().remove_plugin(plugin_id)

    # hooks
    def app_event(self, events, event_type):
        host = self.host
        if host:
            host.app_event(events, event_type)

    def send(self, account):
        host = self.host
        return bool(host and host.send(account))
