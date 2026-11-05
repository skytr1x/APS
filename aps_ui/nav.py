from client_utils import get_last_fragment

from .fragment import APSFragment


class Navigator:
    def __init__(self, ui):
        self.ui = ui
        self.fragments = []

    def remember(self, fragment):
        self.fragments.append(fragment)

    def forget(self, fragment):
        self.fragments = [f for f in self.fragments if f is not fragment]

    def drain(self):
        fragments, self.fragments = list(self.fragments), []
        return fragments

    def refresh(self):
        for fragment in list(self.fragments):
            try:
                if fragment.alive:
                    fragment.render()
            except Exception:
                self.ui.logger.exception('APS: screen refresh failed')

    def _failed(self):
        self.ui.dialogs.alert(self.ui.tr('screen_failed_title'), self.ui.tr('screen_failed_message'))

    def open_screen(self):
        current = get_last_fragment()
        if not current or not self.ui.active:
            return
        fragment = None
        try:
            fragment = APSFragment.new_instance()
            fragment.configure(self.ui, 'plugins')
            self.remember(fragment)
            if current.presentFragment(fragment.java) is False:
                self.forget(fragment)
                self._failed()
        except Exception:
            if fragment:
                self.forget(fragment)
            self.ui.logger.exception('APS: unable to open the native screen')
            self._failed()

    def open_child(self, parent, kind):
        if not parent.alive or not self.ui.active:
            return
        child = APSFragment.new_instance()
        child.configure(self.ui, kind)
        self.remember(child)
        try:
            if parent.presentFragment(child.java) is False:
                self.forget(child)
        except Exception:
            self.forget(child)
            self.ui.logger.exception('APS: navigation failed')
            self._failed()
