from org.telegram.messenger import AndroidUtilities
from org.telegram.ui.ActionBar import Theme


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


def sheet_palette():
    """Dialog colors for the bottom sheet."""
    return {
        'title': color(('key_dialogTextBlack',), 0xff0f0f0f),
        'muted': color(('key_dialogTextGray2', 'key_dialogTextGray3'), 0xff8a8a8a),
        'accent': color(('key_featuredStickers_addButton', 'key_dialogTextBlue'), 0xff3390ec),
        'on_accent': color(('key_featuredStickers_buttonText',), 0xffffffff),
        'link': color(('key_dialogTextBlue', 'key_featuredStickers_addButton'), 0xff3390ec),
    }
