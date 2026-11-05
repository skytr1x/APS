from android.graphics import Typeface
from android.util import TypedValue
from android.view import Gravity
from android.widget import LinearLayout, ProgressBar, TextView
from java import jclass
from org.telegram.ui.ActionBar import Theme
from android_utils import OnClickListener

from .system import restart_app
from .theme import dp, sheet_palette


def text_view(context, value, size, tone, bold=False):
    view = TextView(context)
    view.setText(str(value))
    view.setTextSize(TypedValue.COMPLEX_UNIT_SP, size)
    view.setTextColor(tone)
    if bold:
        view.setTypeface(Typeface.DEFAULT_BOLD)
    return view


class SetupSheet:
    def __init__(self, ui, activity, tr):
        self.ui = ui
        self.activity = activity
        self.tr = tr
        self.listeners = []  # keep listeners alive with their views
        self.sheet = None
        self.stage = 'setup'
        self.label = None
        self.content = LinearLayout(activity)
        self.content.setOrientation(LinearLayout.VERTICAL)
        self.content.setPadding(dp(24), dp(14), dp(24), dp(20))

    # lifecycle
    def show(self):
        builder = jclass('org.telegram.ui.ActionBar.BottomSheet$Builder')(self.activity)
        builder.setCustomView(self.content)
        self.sheet = builder.create()
        self.render_setup()
        self.sheet.show()

    def alive(self):
        try:
            return bool(self.ui.active and self.sheet is not None and self.sheet.isShowing())
        except Exception:
            return False

    def close(self):
        try:
            if self.sheet is not None:
                self.sheet.dismiss()
        except Exception:
            pass
        self.sheet = None
        self.listeners.clear()

    def _cancelable(self, value):
        try:
            self.sheet.setCancelable(value)
            self.sheet.setCanceledOnTouchOutside(value)
        except Exception:
            pass

    # building blocks
    def _reset(self, title, message=None):
        self.content.removeAllViews()
        self.listeners.clear()
        colors = sheet_palette()
        heading = text_view(self.activity, title, 23, colors['title'], True)
        heading.setPadding(0, dp(8), 0, dp(10))
        self.content.addView(heading)
        if message:
            sub = text_view(self.activity, message, 15, colors['muted'])
            sub.setPadding(0, 0, 0, dp(20))
            self.content.addView(sub)

    def _button(self, label, action, primary=False):
        colors = sheet_palette()
        view = text_view(self.activity, label, 16, colors['on_accent'] if primary else colors['link'], True)
        view.setGravity(Gravity.CENTER)
        view.setContentDescription(label)
        view.setMinHeight(dp(48))
        if primary:
            try:
                view.setBackground(Theme.createRoundRectDrawable(dp(12), colors['accent']))
            except Exception:
                view.setBackgroundColor(colors['accent'])
        listener = OnClickListener(lambda _view: action())
        self.listeners.append(listener)
        view.setOnClickListener(listener)
        view.setClickable(True)
        return view

    def _add(self, view, height=48, top=0):
        params = LinearLayout.LayoutParams(-1, dp(height))
        params.topMargin = dp(top)
        self.content.addView(view, params)

    def _progress_bar(self):
        try:
            bar = ProgressBar(self.activity, None, 16842872)  # horizontal style
            bar.setIndeterminate(True)
        except Exception:
            bar = ProgressBar(self.activity)
        try:
            bar.getIndeterminateDrawable().setTint(sheet_palette()['accent'])
        except Exception:
            pass
        return bar

    # stages
    def render_setup(self):
        tr = self.tr
        self.stage = 'setup'
        self._reset(tr('setup_title'), tr('setup_message'))
        self._add(self._button(tr('btn_install'), self._install, True), 50)
        row = LinearLayout(self.activity)
        row.setGravity(Gravity.CENTER)
        row.addView(self._button(tr('btn_skip'), self.close), LinearLayout.LayoutParams(0, dp(48), 1.0))
        row.addView(self._button(tr('btn_source'), self.ui.open_source), LinearLayout.LayoutParams(0, dp(48), 1.0))
        self.content.addView(row, LinearLayout.LayoutParams(-1, -2))

    def render_progress(self, label):
        if self.stage == 'progress' and self.label == label:
            return  # same caption is already shown
        self.stage = 'progress'
        self.label = label
        self._reset(label)
        self._add(self._progress_bar(), 8, 8)
        self._cancelable(False)

    def render_result(self, error=None):
        tr = self.tr
        self._cancelable(True)
        if error:
            self.stage = 'error'
            self._reset(tr('install_failed'), str(error)[:500])
            self._add(self._button(tr('sheet_retry'), self._install, True), 50)
            self._add(self._button(tr('sheet_later'), self.close), 48)
        else:
            self.stage = 'ready'
            self._reset(tr('sheet_done_title'), tr('sheet_done_message'))
            self._add(self._button(tr('btn_restart'), self._restart, True), 50)

    # actions
    def _install(self):
        if not self.ui.tasks.busy:
            self.ui.sdk.install(self)

    def _restart(self):
        try:
            restart_app(self.activity)
        except Exception:
            self.ui.logger.exception('APS: unable to restart the app')
            self.close()
            self.ui.dialogs.alert(self.tr('restart_failed_title'), self.tr('restart_failed_message'))
