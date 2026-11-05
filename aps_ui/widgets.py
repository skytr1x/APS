from android.graphics import Typeface
from android.util import TypedValue
from android.view import Gravity
from android.widget import LinearLayout, TextView
from org.telegram.ui.ActionBar import Theme
from android_utils import OnClickListener

from .theme import card_color, dp, gray_color, text_color


def label(ctx, value, size=15, tone=None, bold=False):
    view = TextView(ctx)
    view.setText(str(value))
    view.setTextSize(TypedValue.COMPLEX_UNIT_DIP, size)
    view.setTextColor(text_color() if tone is None else tone)
    if bold:
        view.setTypeface(Typeface.DEFAULT_BOLD)
    return view


def vertical(ctx):
    view = LinearLayout(ctx)
    view.setOrientation(LinearLayout.VERTICAL)
    return view


def card(ctx):
    view = vertical(ctx)
    view.setPadding(dp(16), dp(14), dp(16), dp(14))
    view.setBackground(Theme.createRoundRectDrawable(dp(12), card_color()))
    return view


def add(parent, view, top=0, bottom=10):
    params = LinearLayout.LayoutParams(-1, -2)
    params.topMargin = dp(top)
    params.bottomMargin = dp(bottom)
    parent.addView(view, params)


def heading(ctx, title):
    view = label(ctx, title, 13, gray_color(), True)
    view.setPadding(dp(4), dp(6), dp(4), dp(8))
    return view


def note(ctx, text):
    view = label(ctx, text, 13, gray_color())
    view.setPadding(dp(4), dp(2), dp(4), dp(10))
    return view


def bind_click(fragment, view, callback):
    listener = OnClickListener(lambda _: callback())
    fragment.listeners.append(listener)  # keep alive with the view
    view.setOnClickListener(listener)
    view.setClickable(True)


def row(fragment, title, sub='', action=None, tone=None):
    ctx = fragment.context
    tile = card(ctx)
    line = LinearLayout(ctx)
    line.setGravity(Gravity.CENTER_VERTICAL)
    lines = vertical(ctx)
    lines.addView(label(ctx, title, 16, tone, True))
    if sub:
        sub_view = label(ctx, sub, 13, gray_color())
        sub_view.setPadding(0, dp(4), 0, 0)
        lines.addView(sub_view)
    line.addView(lines, LinearLayout.LayoutParams(0, -2, 1.0))
    if action:
        line.addView(label(ctx, '›', 24, gray_color()))
        bind_click(fragment, tile, action)
    tile.addView(line)
    add(fragment.content, tile)
    return tile
