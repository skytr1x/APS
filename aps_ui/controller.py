import threading

from android_utils import run_on_ui_thread
from client_utils import get_last_fragment
from file_utils import FilesController
from ui.settings import Text

from core import PLUGIN_EXT, SOURCE_URL
from .dialogs import Dialogs
from .nav import Navigator
from .plugin_flow import PluginFlow
from .sdk_flow import SdkFlow
from .system import open_url
from .tasks import Tasks


class PluginUI:
    def __init__(self, owner, service):
        self.owner = owner
        self.service = service
        self.cancelled = threading.Event()
        self.file_secret = None
        self.dialogs = Dialogs(self)
        self.tasks = Tasks(self)
        self.nav = Navigator(self)
        self.sdk = SdkFlow(self)
        self.plugins = PluginFlow(self)

    @property
    def active(self):
        return bool(self.owner._active)

    @property
    def logger(self):
        return self.owner.logger

    def tr(self, key, **params):
        return self.owner.tr(key, **params)

    def activity(self):
        fragment = get_last_fragment()
        return fragment.getParentActivity() if fragment else None

    def open_source(self):
        try:
            activity = self.activity()
            if activity:
                open_url(activity, SOURCE_URL)
        except Exception:
            self.logger.exception('APS: unable to open source link')

    # lifecycle
    def start(self):
        try:
            self.file_secret = FilesController.register(
                FilesController.FileInfo(ext=PLUGIN_EXT[1:], on_click=self.plugins.file_open))
        except Exception:
            self.logger.exception('APS: failed to register file handler')
        self.on_resume(delay=1000)

    def on_resume(self, delay=300):
        if not self.service.installed() and not self.owner.get_setting('aps_onboarding_seen', False):
            run_on_ui_thread(self.sdk.show_setup, delay)

    def close(self):
        self.cancelled.set()
        if self.file_secret:
            try:
                FilesController.unregister(PLUGIN_EXT[1:], self.file_secret)
            except Exception:
                self.logger.exception('APS: unregister failed')
            self.file_secret = None
        sheet = self.sdk.take_sheet()
        fragments = self.nav.drain()

        def close_ui():
            if sheet:
                sheet.close()
            for fragment in reversed(fragments):
                try:
                    if fragment.alive:
                        fragment.finishFragment()
                except Exception:
                    self.logger.exception('APS: could not close fragment')
        run_on_ui_thread(close_ui)

    # settings
    def settings_entries(self):
        return [Text(text=self.tr('root_plugins'), icon='msg_list', on_click=lambda view: self.nav.open_screen())]
