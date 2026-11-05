from android.view import View
from android.widget import FrameLayout, ScrollView
from org.telegram.messenger import R
from org.telegram.ui.ActionBar import BaseFragment
from extera_utils.classes import Base, java_subclass, joverride

from .listeners import GEAR_ID, NativeMenuClick
from .pages import render_plugins, render_settings
from .theme import dp, page_color
from .widgets import vertical


@java_subclass(BaseFragment)
class APSFragment(Base):
    def __init__(self, *args):
        self.ui = None
        self.kind = 'plugins'
        self.context = None
        self.content = None
        self.menu_click = None
        self.listeners = []
        self.cards = []
        self.alive = True
        self.has_gear = False
        self.query = ''

    def configure(self, ui, kind):
        self.ui = ui
        self.kind = kind

    def t(self, key, **params):
        return self.ui.tr(key, **params) if self.ui else key

    @joverride()
    def getFragmentView(self):
        return getattr(self, '_fragment_view', None)

    @joverride()
    def createView(self, context):
        try:
            self.context = context
            bar = self.getActionBar()
            if bar:
                bar.setBackButtonImage(R.drawable.ic_ab_back)
                bar.setAllowOverlayTitle(True)
                bar.setTitle(self.t('plugins_title' if self.kind == 'plugins' else 'aps_settings_title'))
                callback = NativeMenuClick.new_instance()
                callback.configure(self)
                self.menu_click = callback
                bar.setActionBarMenuOnItemClick(callback.java)
                if self.kind == 'plugins':
                    self._add_gear(bar, context)

            root = FrameLayout(context)
            root.setBackgroundColor(page_color())

            scroll = ScrollView(context)
            scroll.setFillViewport(True)

            self.content = vertical(context)
            self.content.setPadding(dp(12), dp(12), dp(12), dp(16))

            scroll.addView(self.content, FrameLayout.LayoutParams(-1, -2))
            root.addView(scroll, FrameLayout.LayoutParams(-1, -1))

            try:
                self.render()
            except Exception:
                if self.ui and hasattr(self.ui, 'logger'):
                    self.ui.logger.exception('APS: render failed in createView')

            self._fragment_view = root
            return root
        except Exception:
            if self.ui and hasattr(self.ui, 'logger'):
                self.ui.logger.exception('APS: createView failed critically')
            fallback = FrameLayout(context)
            self._fragment_view = fallback
            return fallback

    @joverride()
    def onFragmentDestroy(self):
        self.alive = False
        self.content = None
        self.context = None
        self._fragment_view = None
        self.cards.clear()
        self.listeners.clear()
        self.menu_click = None
        ui, self.ui = self.ui, None
        if ui:
            ui.nav.forget(self)
        super().onFragmentDestroy()

    def _add_gear(self, bar, context):
        try:
            resource = context.getResources().getIdentifier('msg_settings', 'drawable', context.getPackageName())
            if not resource:
                resource = int(R.drawable.msg_settings)
            menu = bar.createMenu()
            menu.clearItems()
            item = menu.addItem(GEAR_ID, int(resource))
            item.setContentDescription(self.t('aps_settings_title'))
            self.has_gear = True
        except Exception:
            self.has_gear = False
            if self.ui:
                self.ui.logger.warning('APS: settings icon unavailable, using a settings row')

    def render(self):
        if (not self.alive or self.content is None or self.context is None
                or self.ui is None or not self.ui.active):
            return
        self.listeners = []
        self.cards = []
        self.content.removeAllViews()
        if self.kind == 'plugins':
            render_plugins(self)
        else:
            render_settings(self)

    def filter(self, query):
        self.query = query
        needle = query.strip().lower()
        for name, tile in self.cards:
            tile.setVisibility(View.VISIBLE if needle in name else View.GONE)
