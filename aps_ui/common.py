from android.graphics import Typeface
from android.util import TypedValue
from android.view import Gravity
from android.widget import LinearLayout, TextView
from org.telegram.messenger import AndroidUtilities
from org.telegram.ui.ActionBar import Theme
from android_utils import OnClickListener


def dp(n):
    return int(AndroidUtilities.dp(n))


def color(names, fallback):
    for name in names:
        try:
            return int(Theme.getColor(getattr(Theme, name)))
        except Exception:
            pass
    return fallback - (1 << 32) if fallback >= 0x80000000 else fallback


def page_color(): return color(('key_windowBackgroundGray',), 0xff101010)
def card_color(): return color(('key_windowBackgroundWhite',), 0xff1c1c1c)
def text_color(): return color(('key_windowBackgroundWhiteBlackText',), 0xfff5f5f5)
def gray_color(): return color(('key_windowBackgroundWhiteGrayText', 'key_windowBackgroundWhiteGrayText2'), 0xff999999)
def accent_color(): return color(('key_windowBackgroundWhiteBlueText', 'key_windowBackgroundWhiteBlueText4'), 0xff3390ec)
def red_color(): return color(('key_text_RedBold', 'key_dialogTextRed', 'key_windowBackgroundWhiteRedText'), 0xffe53935)
def divider_color(): return color(('key_divider', 'key_windowBackgroundGrayLine'), 0x1f808080)


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
