from ui.alert import AlertDialogBuilder
from ui.bulletin import BulletinHelper

from core import error_parts


class Dialogs:
    def __init__(self, ui):
        self.ui = ui

    def error_text(self, exc):
        key, params = error_parts(exc)
        if key:
            return self.ui.tr(key, **params)
        return self.ui.tr('generic_error', error=str(exc))

    def notify(self, text, kind='success'):
        try:
            show = {'success': BulletinHelper.show_success,
                    'error': BulletinHelper.show_error}.get(kind, BulletinHelper.show_info)
            show(text)
        except Exception:
            self.ui.logger.exception('APS: bulletin failed')

    def alert(self, title, message, ok=None, on_ok=None, cancel=None,
              neutral=None, on_neutral=None, danger=False):
        ui = self.ui
        activity = ui.activity()
        if not activity or not ui.active:
            return None
        dialog = AlertDialogBuilder(activity)
        dialog.set_title(title)
        dialog.set_message(message)

        def closing(callback):
            def handler(builder, which):
                builder.dismiss()
                if callback:
                    callback()
            return handler

        dialog.set_positive_button(ok or ui.tr('btn_ok'), closing(on_ok))
        if cancel:
            dialog.set_negative_button(cancel, closing(None))
        if neutral:
            dialog.set_neutral_button(neutral, lambda builder, which: on_neutral())
        dialog.show()
        if danger:
            try:
                dialog.make_button_red(AlertDialogBuilder.BUTTON_POSITIVE)
            except Exception:
                ui.logger.exception('APS: could not style button')
        return dialog

    def spinner(self, activity, title, message):
        dialog = AlertDialogBuilder(activity, AlertDialogBuilder.ALERT_TYPE_SPINNER)
        dialog.set_title(title)
        dialog.set_message(message)
        dialog.show()
        dialog.set_cancelable(False)
        return dialog
