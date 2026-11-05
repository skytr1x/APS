import weakref

from android.widget import CompoundButton
from android.text import TextWatcher
from java import dynamic_proxy
from org.telegram.ui.ActionBar import ActionBar
from extera_utils.classes import Base, java_subclass, joverride

GEAR_ID = 1


@java_subclass(ActionBar.ActionBarMenuOnItemClick)
class NativeMenuClick(Base):
    def __init__(self, *args):
        super().__init__(*args)
        self.fragment_ref = None

    def configure(self, fragment):
        self.fragment_ref = weakref.ref(fragment)

    @joverride()
    def onItemClick(self, item_id):
        fragment = self.fragment_ref() if self.fragment_ref else None
        if fragment is None or not fragment.alive or fragment.ui is None or not fragment.ui.active:
            return
        if int(item_id) == -1:
            fragment.finishFragment()
        elif int(item_id) == GEAR_ID and fragment.kind == 'plugins':
            fragment.ui.open_child(fragment, 'settings')


class PluginSwitch(dynamic_proxy(CompoundButton.OnCheckedChangeListener)):
    def __init__(self, fragment, plugin_id):
        super().__init__()
        self.fragment_ref = weakref.ref(fragment)
        self.plugin_id = plugin_id
        self.busy = False

    def onCheckedChanged(self, button, checked):
        fragment = self.fragment_ref()
        if (self.busy or fragment is None or not fragment.alive
                or fragment.ui is None or not fragment.ui.active):
            return
        self.busy = True
        try:
            if not fragment.ui.toggle(self.plugin_id, bool(checked)):
                button.setChecked(False)
        finally:
            self.busy = False


class SearchChanged(dynamic_proxy(TextWatcher)):
    def __init__(self, fragment):
        super().__init__()
        self.fragment_ref = weakref.ref(fragment)

    def beforeTextChanged(self, s, start, count, after): pass

    def onTextChanged(self, s, start, before, count):
        fragment = self.fragment_ref()
        if fragment is not None and fragment.alive:
            fragment.filter(str(s or ''))

    def afterTextChanged(self, s): pass
