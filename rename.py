"""Rename selected object's in Maya scene.

This script creates a UI that allows the user to edit an objects name. You can
add or remove digits from a name, as well as search and replace keywords. Or even
replace the name entirely.

The history is stored allowing you to easily undo all name changes.

Compatible with Python 3.7.7
"""

__all__ = ["launch"]
__author__ = 'Ross Harrop'
__version__ = '1.0.0'

# Standard
import os

# Third party
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import maya.cmds as mc

# Local
from .utils import *


class GizmoRenameUI(MayaQWidgetDockableMixin, QMainWindow):
    """Main UI that user interacts with."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(250, 400)

        # setup status bar to display messages to users
        self.status_bar = QStatusBar(self)
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet("QStatusBar {color: orange}")
        self.status_bar.showMessage("opened")
        self.setStatusBar(self.status_bar)
        self.setup()

    def setup(self):
        """Main UI setup"""

        # Central widget for QMainWindow
        central_widget = QWidget(self)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Name option layout
        name_grp = GroupBoxColour("Name")
        name_grp.setStatusTip("replace name on object(s)")
        name_grp.message.connect(
            lambda x: self.status_bar.showMessage(x)
        )
        self.name_lyt = GroupLineEdit()
        self.name_lyt.userEdit.connect(
            lambda x: setattr(name_grp, 'active', x)
        )
        name_grp.setLayout(self.name_lyt)

        # Add option layout
        add_grp = GroupBoxColour("Add")
        add_grp.setStatusTip("add prefix and/or suffix to your object(s).")
        add_grp.message.connect(
            lambda x: self.status_bar.showMessage(x)
        )
        add_lyt = QVBoxLayout()
        add_grp.setLayout(add_lyt)
        self.prefix_lyt = GroupLineEdit('Prefix')
        self.suffix_lyt = GroupLineEdit('Suffix')
        self.prefix_lyt.userEdit.connect(
            lambda: setattr(add_grp, 'active', self.get_state(self.prefix_lyt, self.suffix_lyt))
        )
        self.suffix_lyt.userEdit.connect(
            lambda: setattr(add_grp, 'active', self.get_state(self.prefix_lyt, self.suffix_lyt))
        )
        add_lyt.addLayout(self.prefix_lyt)
        add_lyt.addLayout(self.suffix_lyt)

        # Remove option layout
        remove_grp = GroupBoxColour('Remove')
        remove_grp.setStatusTip("remove digits from start and/or end of objects(s).")
        remove_grp.message.connect(
            lambda x: self.status_bar.showMessage(x)
        )
        r_layout = QVBoxLayout()
        remove_grp.setLayout(r_layout)
        self.s_layout = GroupSpinBox(label='First')
        r_layout.addLayout(self.s_layout)
        self.e_layout = GroupSpinBox(label='End')
        r_layout.addLayout(self.e_layout)
        self.s_layout.userEnabled.connect(
            lambda: setattr(remove_grp, 'active', self.get_state(self.s_layout, self.e_layout))
        )
        self.e_layout.userEnabled.connect(
            lambda: setattr(remove_grp, 'active', self.get_state(self.s_layout, self.e_layout))
        )
        r_layout.addStretch(1)

        # Search and Replace option layout
        replace_grp = GroupBoxColour('Search/Replace')
        replace_grp.setStatusTip("search and replace key words in your name.")
        replace_grp.message.connect(
            lambda x: self.status_bar.showMessage(x)
        )
        self.sr_lyt = GroupSearchReplaceWidget()
        replace_grp.setLayout(self.sr_lyt)

        self.sr_lyt.userEnabled.connect(
            lambda x: setattr(replace_grp, 'active', x)
        )

        # Button layout
        go_button = QPushButton("RENAME SELECTED")
        go_button.setFixedHeight(30)
        go_button.setStyleSheet("QPushButton {background-color: orange; "
                                "color: black; "
                                "font-size: 8pt;"
                                "font-weight: bold;} ")
        go_button.clicked.connect(self.rename_selected)

        main_layout.addWidget(name_grp)
        main_layout.addWidget(add_grp)
        main_layout.addWidget(remove_grp)
        main_layout.addWidget(replace_grp)
        main_layout.addWidget(go_button)

    @staticmethod
    def get_state(*widgets):
        """Check if any widgets are enabled.

        Custom widgets in this file has an 'enabled' parameter for conveniance.
        Args:
            *widgets(QWidget): widget to check custom function on

        Returns:
        """
        return True if any(w.user_enabled for w in widgets) else False

    @undo_chunk
    def rename_selected(self):
        """Rename objects in scene"""

        sel = mc.ls(sl=1) or []

        if not sel:
            self.status_bar.showMessage("nothing selected in scene!")
            return

        # Build key word arguments
        kwargs = {}
        if self.name_lyt.user_enabled:
            kwargs['name'] = self.name_lyt.user_text

        if self.prefix_lyt.user_enabled:
            kwargs['prefix'] = self.prefix_lyt.user_text

        if self.suffix_lyt.user_enabled:
            kwargs['suffix'] = self.suffix_lyt.user_text

        if self.s_layout.user_enabled:
            kwargs['remove_start'] = self.s_layout.user_value

        if self.e_layout.user_enabled:
            kwargs['remove_end'] = self.e_layout.user_value

        if self.sr_lyt.user_enabled:
            kwargs['search_replace'] = self.sr_lyt.search_replace

        if not kwargs:
            self.status_bar.showMessage("no options selected in UI!")
            return

        for s in sel:
            name = rename_string(s, **kwargs)
            mc.rename(s, name)

        self.status_bar.showMessage(f"Renamed {len(sel)} object(s)")


class GroupBoxColour(QGroupBox):
    """Custom QGroupBox to handle events and stylesheets"""

    message = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = False
        self.setMouseTracking(True)
        self.set_style(False)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        self.set_style(value)

    def set_style(self, is_active):
        """
        Change border colour if user has enabled the option.

        Args:
            is_active(bool): is the option being used.
        """

        colour = 'grey'
        if is_active:
            colour = 'orange'

        title_style = "QGroupBox:title {subcontrol-position: top margin; padding: -15px 1px 0px 1px;}"
        border_style = "QGroupBox {border: 2px solid " + colour + "; border-radius: 5px; margin-top: 3ex;}"

        self.setStyleSheet(border_style + title_style)

    def enterEvent(self, event):
        """When mouse is over the widget display information"""
        self.message.emit(self.statusTip())
        return super().enterEvent(event)


class GroupLineEdit(QHBoxLayout):
    """Custom class to group QCheckBox and QLineEdit.

    Added custom Signal to help de-clutter main UI.
    """

    user_text = None
    userEdit = Signal(bool)

    def __init__(self, label=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_enabled = False

        if label:
            _label = QLabel(label)
            self.addWidget(_label)

        self.line_edit = QLineEdit()
        self.line_edit.setEnabled(False)
        self.line_edit.textChanged.connect(
            lambda x: setattr(self, 'user_text', x)
        )

        check = QCheckBox()
        check.stateChanged.connect(
            lambda x: setattr(self, 'user_enabled', x)
        )

        self.addWidget(self.line_edit)
        self.addWidget(check)

    @property
    def user_enabled(self):
        return self._user_enabled

    @user_enabled.setter
    def user_enabled(self, value):
        self._user_enabled = value
        self.userEdit.emit(value)
        self.line_edit.setEnabled(value)


class GroupSpinBox(QHBoxLayout):
    """Custom class to group QCheckBox and QSpinBox.

    Added custom Signal to help de-clutter main UI.
    """

    user_value = None
    userEnabled = Signal(bool)

    def __init__(self, label='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_enabled = False

        self.setContentsMargins(2, 2, 2, 2)
        s_label = QLabel(label)
        s_label.setMinimumWidth(25)
        self.spin_box = QSpinBox()
        self.spin_box.setEnabled(False)
        self.spin_box.textChanged.connect(
            lambda x: setattr(self, 'user_value', int(x))
        )
        _label = QLabel("Digit(s)")
        s_check = QCheckBox()
        s_check.stateChanged.connect(
            lambda x: setattr(self, 'user_enabled', x)
        )

        self.addWidget(s_label)
        self.addWidget(self.spin_box)
        self.addWidget(_label)
        self.addWidget(s_check)
        self.addStretch(1)

    @property
    def user_enabled(self):
        return self._user_enabled

    @user_enabled.setter
    def user_enabled(self, value):
        self._user_enabled = value
        self.spin_box.setEnabled(value)
        self.userEnabled.emit(value)


class GroupSearchReplaceWidget(QVBoxLayout):
    """Custom class to group QCheckBox and multiple QLineEdit.

    Added custom Signal to help de-clutter main UI.
    """

    search_replace = []
    userEnabled = Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_enabled = False

        search_layout = QHBoxLayout()
        search_label = QLabel('Search')
        search_label.setMinimumWidth(40)
        self.search_text = QLineEdit()
        self.search_text.setEnabled(False)
        search_check = QCheckBox()
        search_check.stateChanged.connect(
            lambda x: setattr(self, 'user_enabled', x)
        )
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_text)
        search_layout.addWidget(search_check)
        search_layout.addStretch(1)
        self.addLayout(search_layout)

        replace_layout = QHBoxLayout()
        replace_label = QLabel('Replace')
        replace_label.setMinimumWidth(40)
        self.replace_text = QLineEdit()
        self.replace_text.setEnabled(False)
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_text)
        replace_layout.addStretch(1)

        self.search_text.textChanged.connect(
            lambda x: self.create_args(x, self.replace_text.text())
        )
        self.replace_text.textChanged.connect(
            lambda x: self.create_args(self.search_text.text(), x)
        )

        self.addLayout(replace_layout)

    @property
    def user_enabled(self):
        return self._user_enabled

    @user_enabled.setter
    def user_enabled(self, value):
        self._user_enabled = value
        self.replace_text.setEnabled(value)
        self.search_text.setEnabled(value)
        self.userEnabled.emit(value)

    def create_args(self, search_text, replace_text):
        """Create list of tuples for search and replace.

        Filter user input to pair up keywords from search
        and replace fields.
        """

        items = []
        search_terms = search_text.replace(" ", "").split(',')
        replace_terms = replace_text.replace(" ", "").split(',')
        for pair in zip(search_terms, replace_terms):
            items.append(pair)

        self.search_replace = items


def rename_string(obj, name='', prefix='', suffix='', remove_start=None, remove_end=None, search_replace=None):
    """Rename selected object in scene.

    Args:
        obj(str): target object.
        name(str): replace existing name with this one.
        prefix(str): add text at the beginning.
        suffix(str): add test at the end.
        remove_start: remove x ammount of digit from the begining.
        remove_end: remove x ammount of digits from the end.
        search_replace([(str, str)]): search and replace keywords, each tuple is a separate check.

    Returns:
        name(str): new name after user changes.
    """
    if search_replace is None:
        search_replace = [('', '')]
    if name:
        obj = name

    if remove_start and remove_end:
        obj = obj[remove_start:(remove_end * -1)]
    elif remove_start and not remove_end:
        obj = obj[remove_start:]
    elif not remove_start and remove_end:
        obj = obj[:(remove_end * -1)]
    else:
        pass

    for search, replace in search_replace:
        obj = obj.replace(search, replace)

    if prefix:
        obj = f"{prefix}{obj}"

    if suffix:
        obj += suffix

    return obj


def launch():
    """Remove any existing windows and launch."""

    win_name = 'gizmo_rename_win'
    if mc.window(win_name, exists=True):
        mc.deleteUI(win_name)

    win = GizmoRenameUI()
    win.setWindowTitle('Gizmo Rename')
    win.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "media/gizmo-dark-icon.png")))
    win.setObjectName(win_name)
    win.show()
    return win
