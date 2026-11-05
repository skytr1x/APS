from android.text import TextUtils
from android.util import TypedValue
from android.view import Gravity, View
from android.widget import EditText, LinearLayout, Switch

from .listeners import PluginSwitch, SearchChanged
from .theme import accent_color, divider_color, dp, gray_color, red_color, text_color
from .widgets import add, bind_click, card, heading, label, note, row


def _search_box(fragment):
    ctx, t = fragment.context, fragment.t
    search = EditText(ctx)
    search.setSingleLine(True)
    search.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 16)
    search.setTextColor(text_color())
    search.setHintTextColor(gray_color())
    search.setHint(str(t('plugins_search_hint') or 'Search'))
    watcher = SearchChanged(fragment)
    fragment.listeners.append(watcher)
    search.addTextChangedListener(watcher)
    return search


def _plugin_card(fragment, name):
    ctx, ui, t = fragment.context, fragment.ui, fragment.t
    tile = card(ctx)
    head = LinearLayout(ctx)
    head.setGravity(Gravity.CENTER_VERTICAL)
    title = label(ctx, str(name or ''), 20, text_color(), True)
    title.setMaxLines(1)
    title.setEllipsize(TextUtils.TruncateAt.END)
    head.addView(title, LinearLayout.LayoutParams(0, -2, 1.0))
    toggle = Switch(ctx)
    toggle.setContentDescription(str(t('plugin_toggle_desc', name=name) or 'Toggle'))
    toggle.setChecked(ui.service.enabled(name))
    listener = PluginSwitch(fragment, name)
    fragment.listeners.append(listener)
    toggle.setOnCheckedChangeListener(listener)
    head.addView(toggle)
    tile.addView(head)

    sub_text = t('plugin_row_sub')
    if sub_text:
        subtitle = label(ctx, str(sub_text), 13, gray_color())
        subtitle.setPadding(0, dp(6), 0, 0)
        tile.addView(subtitle)

    trust_text = t('plugin_trust_note')
    if trust_text:
        warning = label(ctx, str(trust_text), 14, text_color())
        warning.setPadding(0, dp(14), 0, dp(12))
        tile.addView(warning)

    line = View(ctx)
    line.setBackgroundColor(divider_color())
    tile.addView(line, LinearLayout.LayoutParams(-1, dp(1)))

    actions = LinearLayout(ctx)
    actions.setGravity(Gravity.CENTER_VERTICAL)
    info_text = t('action_info')
    if info_text:
        info = label(ctx, str(info_text), 14, accent_color(), True)
        info.setPadding(dp(8), dp(12), dp(8), dp(4))
        bind_click(fragment, info, lambda: ui.plugins.info(name))
        actions.addView(info, LinearLayout.LayoutParams(0, -2, 1.0))

    remove_text = t('action_remove')
    if remove_text:
        remove = label(ctx, str(remove_text), 14, red_color(), True)
        remove.setPadding(dp(8), dp(12), dp(8), dp(4))
        bind_click(fragment, remove, lambda: ui.plugins.confirm_remove(name))
        actions.addView(remove)

    tile.addView(actions)
    return tile


def render_plugins(fragment):
    ctx, ui, t = fragment.context, fragment.ui, fragment.t
    names = ui.service.ids() if hasattr(ui, 'service') else []

    def st(key, default=''):
        try:
            res = t(key)
            return str(res) if res is not None else default
        except Exception:
            return default

    if not fragment.has_gear:
        row(fragment, st('aps_settings_title', 'Settings'), st('settings_row_sub', ''), lambda: ui.nav.open_child(fragment, 'settings'))

    if hasattr(ui, 'service') and not ui.service.installed():
        row(fragment, st('plugins_need_sdk', 'SDK Required'), st('plugins_need_sdk_sub', ''), getattr(ui.sdk, 'ask_install', None), accent_color())

    if not names:
        h_text = st('plugins_installed', 'Plugins')
        if h_text:
            add(fragment.content, heading(ctx, h_text.upper()), bottom=0)
        row(fragment, st('plugins_none', 'No plugins'), st('plugins_none_sub', ''))
        return

    search = _search_box(fragment)
    add(fragment.content, search, bottom=8)

    h_text = st('plugins_installed', 'Plugins')
    if h_text:
        add(fragment.content, heading(ctx, h_text.upper()), bottom=0)

    for name in names:
        tile = _plugin_card(fragment, name)
        if tile:
            add(fragment.content, tile)
            fragment.cards.append((str(name).lower(), tile))

    hint_text = st('plugins_add_hint', '')
    if hint_text:
        add(fragment.content, note(ctx, hint_text), bottom=0)

    if fragment.query:
        search.setText(fragment.query)
        fragment.filter(fragment.query)


def render_settings(fragment):
    ctx, ui, t = fragment.context, fragment.ui, fragment.t
    sdk = getattr(ui, 'sdk', None)

    try:
        if sdk and hasattr(sdk, 'ensure_release'):
            sdk.ensure_release()
    except Exception:
        pass

    state = ui.service.state() if hasattr(ui, 'service') else 'missing'

    def st(key, default=''):
        try:
            res = t(key)
            return str(res) if res is not None else default
        except Exception:
            return default

    sdk_title = st('section_sdk', 'SDK')
    if sdk_title:
        add(fragment.content, heading(ctx, sdk_title.upper()), bottom=0)

    row(fragment, st('section_status', 'Status'), "Установлена версия 1.0.0")

    release_text = str(sdk.release_text()) if sdk and hasattr(sdk, 'release_text') and sdk.release_text() is not None else "1.0.0"
    recheck_release = getattr(sdk, 'recheck_release', None)
    row(fragment, st('release_row', 'Release'), release_text, recheck_release)

    note_text = st('release_note', '')
    if note_text:
        add(fragment.content, note(ctx, note_text), bottom=6)

    ask_install = getattr(sdk, 'ask_install', None)
    if state == 'ready':
        row(fragment, st('update_row', 'Update'), st('update_row_sub', ''), ask_install)
    else:
        row(fragment, st('install_row', 'Install'), st('install_row_sub', ''), ask_install, accent_color())

    ask_remove = getattr(sdk, 'ask_remove', None)
    if state != 'missing':
        row(fragment, st('remove_row', 'Remove'), st('remove_row_sub', ''), ask_remove, red_color())

    exp_note = st('experimental_note', '')
    if exp_note:
        add(fragment.content, note(ctx, exp_note), bottom=0)
