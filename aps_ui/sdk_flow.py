from android_utils import run_on_ui_thread
from client_utils import run_on_queue

from core import DEV
from .sheet import SetupSheet


class SdkFlow:
    def __init__(self, ui):
        self.ui = ui
        self.sheet = None
        self.release = None
        self.release_loading = False

    # setup
    def show_setup(self, *_, force=False):
        ui = self.ui
        if not ui.active or ui.service.installed() or ui.tasks.busy:
            return
        if self.sheet is not None and self.sheet.alive():
            return
        if not force and ui.owner.get_setting('aps_onboarding_seen', False):
            return
        activity = ui.activity()
        if not activity:
            return
        try:
            sheet = SetupSheet(ui, activity, ui.tr)
            sheet.show()
            self.sheet = sheet
        except Exception:
            ui.logger.exception('APS: BottomSheet unavailable, using dialog fallback')
            if not ui.dialogs.alert(ui.tr('setup_title'), ui.tr('setup_message'),
                                    ok=ui.tr('btn_install'), on_ok=self.install,
                                    cancel=ui.tr('btn_skip'),
                                    neutral=ui.tr('btn_source'), on_neutral=ui.open_source):
                return
        ui.owner.set_setting('aps_onboarding_seen', True)

    def take_sheet(self):
        sheet, self.sheet = self.sheet, None
        return sheet

    # install
    def ask_install(self):
        ui = self.ui
        if ui.service.installed():
            ui.dialogs.alert(ui.tr('update_title'), ui.tr('install_message'),
                             ok=ui.tr('btn_update'), on_ok=self.install, cancel=ui.tr('btn_cancel'))
        else:
            self.show_setup(force=True)

    def install(self, sheet=None):
        ui = self.ui

        def work(update):
            ui.service.install(progress=lambda key: update(ui.tr(key)), cancelled=ui.cancelled.is_set)
        ui.tasks.run('install', ui.tr('progress_installing'), ui.tr('installing_message'), work,
                     lambda: ui.dialogs.notify(ui.tr('install_done')), ui.tr('install_failed'), sheet=sheet)

    # remove
    def ask_remove(self):
        ui = self.ui
        if ui.tasks.blocked():
            return
        if ui.service.state() == 'missing':
            ui.dialogs.notify(ui.tr('sdk_missing'), 'info')
            return
        message = ui.tr('remove_message')
        count = len(ui.service.enabled_ids())
        if count:
            message += '\n\n' + ui.tr('remove_enabled_note', count=count)
        ui.dialogs.alert(ui.tr('remove_title'), message, ok=ui.tr('btn_remove'), on_ok=self.remove,
                         cancel=ui.tr('btn_cancel'), danger=True)

    def remove(self):
        ui = self.ui

        def work(update):
            ui.service.remove()
        ui.tasks.run('remove', ui.tr('removing_title'), ui.tr('removing_message'), work,
                     lambda: ui.dialogs.notify(ui.tr('remove_done')), ui.tr('remove_failed'),
                     fail_note=ui.tr('remove_failed_note'), prepare=ui.service.disable_all)

    # release
    def ensure_release(self):
        ui = self.ui
        if self.release is not None or self.release_loading or not ui.active:
            return
        self.release_loading = True

        def worker():
            try:
                version = ui.service.latest_release()
            except Exception:
                version = DEV

            def finish():
                self.release_loading = False
                if not ui.active:
                    return
                self.release = version
                ui.nav.refresh()
            run_on_ui_thread(finish)
        run_on_queue(worker)

    def recheck_release(self):
        if self.release_loading:
            return
        self.release = None
        self.ensure_release()
        run_on_ui_thread(self.ui.nav.refresh)

    # texts
    def status_text(self):
        ui = self.ui
        state = ui.service.state()
        if state != 'ready':
            return ui.tr('sdk_' + state)
        manifest = ui.service.manifest()
        parts = [ui.tr('sdk_ready'), 'ABI ' + str(manifest.get('abi'))]
        if manifest.get('version'):
            parts.append('v' + str(manifest['version']))
        return ' · '.join(parts)

    def release_text(self):
        if self.release is None:
            return self.ui.tr('release_checking')
        return self.ui.tr('release_dev') if self.release == DEV else self.release
