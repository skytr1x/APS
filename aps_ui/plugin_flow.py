import os

from android_utils import run_on_ui_thread


class PluginFlow:
    def __init__(self, ui):
        self.ui = ui

    # import
    def file_open(self, args):
        ui = self.ui
        if not ui.active:
            return
        path = str(args.file.getAbsolutePath())

        def ask():
            ui.dialogs.alert(ui.tr('import_title'), ui.tr('import_message', name=os.path.basename(path)),
                             ok=ui.tr('btn_add'), on_ok=lambda: self.import_file(path),
                             cancel=ui.tr('btn_cancel'))
        run_on_ui_thread(ask)

    def import_file(self, path):
        ui = self.ui
        try:
            name = ui.service.import_plugin(path)
        except Exception as exc:
            ui.dialogs.alert(ui.tr('import_failed'), ui.dialogs.error_text(exc))
            return
        ui.nav.refresh()
        ui.dialogs.notify(ui.tr('plugin_added', name=name))

    # state
    def toggle(self, name, enabled):
        """Return False when the switch must go back to off."""
        ui = self.ui
        if enabled and ui.tasks.busy == 'remove':
            ui.dialogs.notify(ui.tr('busy_removing'), 'info')
            ui.service.set_enabled(name, False)
            return False
        try:
            ui.service.toggle(name, enabled)
        except Exception as exc:
            ui.logger.exception('APS: toggle failed')
            ui.dialogs.alert(ui.tr('toggle_error_title'), ui.dialogs.error_text(exc))
            return False
        return True

    def info(self, name):
        ui = self.ui
        state = ui.tr('state_on' if ui.service.enabled(name) else 'state_off')
        ui.dialogs.alert(name, ui.tr('plugin_info_message', state=state))

    def confirm_remove(self, name):
        ui = self.ui

        def remove():
            try:
                ui.service.remove_plugin(name)
                ui.nav.refresh()
                ui.dialogs.notify(ui.tr('plugin_removed', name=name))
            except Exception as exc:
                ui.logger.exception('APS: plugin removal failed')
                ui.dialogs.alert(ui.tr('plugin_remove_failed'), ui.dialogs.error_text(exc))
        ui.dialogs.alert(ui.tr('plugin_remove_title'), ui.tr('plugin_remove_message', name=name),
                         ok=ui.tr('btn_remove'), on_ok=remove, cancel=ui.tr('btn_cancel'), danger=True)
