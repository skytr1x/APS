import os
from typing import Any

from base_plugin import AppEvent, BasePlugin, HookResult, HookStrategy
from elyx import strings
from file_utils import get_files_dir

from core import PluginService
from aps_ui.controller import PluginUI

HOOKS = ()

# higher priority runs first
SEND_PRIORITY = 0


def tr(key, **params):
    return strings(key, **params)


class AnotherPluginSystem(BasePlugin):
    tr = staticmethod(tr)

    # lifecycle
    def on_plugin_load(self):
        self._active = True
        home = os.path.join(get_files_dir(), 'another_plugin_system')
        self._service = PluginService(home, self.get_setting, self.set_setting, self.logger)
        self._ui = PluginUI(self, self._service)
        self._service.load()
        self.add_on_send_message_hook(SEND_PRIORITY)
        for name, substring, priority in HOOKS:
            self.add_hook(name, substring, priority)
        self._ui.start()

    def on_plugin_unload(self):
        self._active = False
        self._ui.close()
        self._service.close()

    def on_app_event(self, event_type: AppEvent):
        if not self._active:
            return
        if event_type == AppEvent.RESUME:
            self._ui.on_resume()
        try:
            self._service.app_event(AppEvent, event_type)
        except Exception:
            self.logger.exception('APS: app event hook failed')

    def create_settings(self):
        return self._ui.settings_entries()

    # message hook
    def on_send_message_hook(self, account: int, params: Any) -> HookResult:
        try:
            if self._service.send(account):
                return HookResult(strategy=HookStrategy.CANCEL)
        except Exception:
            self.logger.exception('APS: send hook failed, passing through')
        return HookResult()

    # request hooks
    def pre_request_hook(self, request_name: str, account: int, request: Any) -> HookResult:
        return HookResult()

    def post_request_hook(self, request_name: str, account: int, response: Any, error: Any) -> HookResult:
        return HookResult()

    # update hooks
    def on_update_hook(self, update_name: str, account: int, update: Any) -> HookResult:
        return HookResult()

    def on_updates_hook(self, container_name: str, account: int, updates: Any) -> HookResult:
        return HookResult()
