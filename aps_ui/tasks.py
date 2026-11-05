from android_utils import run_on_ui_thread
from client_utils import run_on_queue


class Tasks:
    def __init__(self, ui):
        self.ui = ui
        self.busy = ''

    def blocked(self):
        if not self.busy:
            return False
        ui = self.ui
        ui.dialogs.notify(ui.tr('busy_removing' if self.busy == 'remove' else 'busy'), 'info')
        return True

    def run(self, kind, title, message, work, on_success, fail_title, fail_note='',
            prepare=None, sheet=None):
        ui = self.ui
        if not ui.active:
            return
        if self.blocked():
            return
        activity = sheet.activity if sheet else ui.activity()
        if not activity:
            return
        self.busy = kind
        try:
            if prepare:
                prepare()
        except Exception:
            self.busy = ''
            ui.logger.exception('APS: task preparation failed')
            return

        progress = None
        if sheet is not None:
            sheet.render_progress(title)
        else:
            progress = ui.dialogs.spinner(activity, title, message)

        def update(text):
            def apply():
                if not ui.active:
                    return
                if sheet is not None:
                    if sheet.alive():
                        sheet.render_progress(text)
                else:
                    progress.set_title(text)
            run_on_ui_thread(apply)

        def job():
            error = None
            try:
                work(update)
            except Exception as exc:
                error = exc
                ui.logger.exception('APS: background task failed')

            def finish():
                self.busy = ''
                if progress is not None:
                    try:
                        progress.dismiss()
                    except Exception:
                        pass
                if not ui.active:
                    return
                ui.nav.refresh()
                text = None if error is None else ui.dialogs.error_text(error)
                if sheet is not None and sheet.alive():
                    sheet.render_result(text)
                elif error is None:
                    on_success()
                else:
                    ui.dialogs.alert(fail_title, text + '\n' + fail_note if fail_note else text)
            run_on_ui_thread(finish)
        run_on_queue(job)
