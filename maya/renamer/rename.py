"""Rename selected object's in Maya scene.

This script creates a UI that allows the user to edit an objects name. You can
add or remove digits from a name, as well as search and replace keywords. Or even
replace the name entirely.

The history is stored allowing you to easily undo all name changes.
"""
import re
import maya.cmds as mc
from PySide2.QtCore import Signal
from PySide2.QtWidgets import *

from ..utils import widgets
from .. import utils


class GizmoRenameUI(widgets.GMainWindow):
    """Main UI that user interacts with."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Renamer v1.0')
        self.setFixedSize(276, 500)
        self._prefix_line_edit = None
        self._suffix_line_edit = None
        self._name_lyt = None
        self._start_spin_box = None
        self._end_spin_box = None
        self.sr_lyt = None
        self.setup()
        self.do_filter_child_events()

    def setup(self):
        """Main UI setup"""

        # Central widget for QMainWindow
        central_widget = QWidget(self)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Name option layout
        name_grp = widgets.GroupBoxText("Name")
        name_grp.setStatusTip("replace name on object(s)")
        self._name_lyt = GroupLineEdit()
        self._name_lyt.userEdit.connect(
            lambda x: setattr(name_grp, 'active', x)
        )
        name_grp.setLayout(self._name_lyt)

        # Add option layout
        add_grp = widgets.GroupBoxText("Add")
        add_grp.setStatusTip("add prefix and/or suffix to your object(s).")

        add_lyt = QVBoxLayout()
        add_grp.setLayout(add_lyt)
        self._prefix_line_edit = GroupLineEdit('Prefix')
        self._suffix_line_edit = GroupLineEdit('Suffix')
        self._prefix_line_edit.userEdit.connect(
            lambda: setattr(add_grp, 'active', self.get_state(self._prefix_line_edit, self._suffix_line_edit))
        )
        self._suffix_line_edit.userEdit.connect(
            lambda: setattr(add_grp, 'active', self.get_state(self._prefix_line_edit, self._suffix_line_edit))
        )
        add_lyt.addLayout(self._prefix_line_edit)
        add_lyt.addLayout(self._suffix_line_edit)

        # Remove option layout
        remove_grp = widgets.GroupBoxText('Remove')
        remove_grp.setStatusTip("remove digits from start and/or end of objects(s).")
        r_layout = QVBoxLayout()
        remove_grp.setLayout(r_layout)
        self._start_spin_box = GroupSpinBox(label='First')
        r_layout.addLayout(self._start_spin_box)
        self._end_spin_box = GroupSpinBox(label='End')
        r_layout.addLayout(self._end_spin_box)
        self._start_spin_box.userEnabled.connect(
            lambda: setattr(remove_grp, 'active', self.get_state(self._start_spin_box, self._end_spin_box))
        )
        self._end_spin_box.userEnabled.connect(
            lambda: setattr(remove_grp, 'active', self.get_state(self._start_spin_box, self._end_spin_box))
        )
        # r_layout.addStretch(1)

        # Search and Replace option layout
        replace_grp = widgets.GroupBoxText('Search/Replace')
        replace_grp.setStatusTip("search and replace key words in your name.")
        self.sr_lyt = GroupSearchReplaceWidget()
        replace_grp.setLayout(self.sr_lyt)

        self.sr_lyt.userEnabled.connect(
            lambda x: setattr(replace_grp, 'active', x)
        )

        # Button layout
        go_button = QPushButton("RENAME SELECTED")
        go_button.setFixedHeight(30)
        go_button.clicked.connect(self.rename_selected)

        oder_btn = QPushButton("Re-Index")
        oder_btn.clicked.connect(self.re_order)
        oder_btn.setFixedHeight(30)

        main_layout.addWidget(name_grp)
        main_layout.addWidget(add_grp)
        main_layout.addWidget(remove_grp)
        main_layout.addWidget(replace_grp)
        main_layout.addWidget(go_button)
        main_layout.addWidget(oder_btn)

    @staticmethod
    def get_state(*widgets: QWidget) -> bool:
        """Check if any widgets are enabled.

        Custom widgets in this file have an 'enabled' parameter for convenience.
        Args:
            *widgets: widget to check custom function on

        Returns:

        """
        return True if any(w.user_enabled for w in widgets) else False

    @utils.undo_chunk
    def rename_selected(self):
        """Rename objects in scene"""

        # Re-order duplicate names so child names are first
        sel = mc.ls(selection=True, long=True) or []
        sel.sort(key=lambda obj: obj.count('|'), reverse=True)

        if not sel:
            self.status_bar.showMessage("nothing selected in scene!")
            return

        # Build key word arguments
        kwargs = {}
        if self._name_lyt.user_enabled:
            kwargs['name'] = self._name_lyt.user_text

        if self._prefix_line_edit.user_enabled:
            kwargs['prefix'] = self._prefix_line_edit.user_text

        if self._suffix_line_edit.user_enabled:
            kwargs['suffix'] = self._suffix_line_edit.user_text

        if self._start_spin_box.user_enabled:
            kwargs['remove_start'] = self._start_spin_box.user_value

        if self._end_spin_box.user_enabled:
            kwargs['remove_end'] = self._end_spin_box.user_value

        if self.sr_lyt.user_enabled:
            kwargs['search_replace'] = self.sr_lyt.search_replace

        if not kwargs:
            self.status_bar.showMessage("no options selected in UI!")
            return

        new_names = []
        for s in sel:
            words = s.split('|') or [s]
            name = utils.rename_string(words[-1], **kwargs)
            mc.rename(s, name)
            new_names.append(name)

        if not self.increment_unique:
            for n in new_names:
                if len(mc.ls(f'{n[:-1]}*')) >= 2:
                    continue
                mc.rename(n, n[:-3])

        self.status_bar.showMessage(f"Renamed {len(sel)} object(s)")

    @utils.undo_chunk
    def re_order(self) -> None:
        """Re-index selected objects in hierarchy order"""
        # Todo: update so user selection doesn't define the order
        # selected joints should be checked an placed into heirarchy order

        sel = mc.ls(selection=True, long=True) or []

        if not sel:
            self.status_bar.showMessage("nothing selected in scene!")
            return

        for i, x in zip(range(len(sel), 0, -1), reversed(sel)):
            s = x.split("|")[-1]
            pattern = re.compile(r'\d+$')
            match = pattern.search(s)
            if not match:
                mc.rename(x, s + str(i).zfill(2))

            if match:
                original = match.group(0)
                _index = int(original) + 1
                new_str = s[:len(original) * -1] + str(i).zfill(2)
                mc.rename(x, new_str)


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
        self.line_edit.textChanged.connect(lambda x: setattr(self, 'user_text', x))

        check = QCheckBox()
        check.stateChanged.connect(lambda x: setattr(self, 'user_enabled', x))

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
        self.spin_box.textChanged.connect(lambda x: setattr(self, 'user_value', int(x)))
        _label = QLabel("Digit(s)")
        s_check = QCheckBox()
        s_check.stateChanged.connect(lambda x: setattr(self, 'user_enabled', x))

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


def launch():
    """Remove any existing windows and launch."""
    win_name = 'gizmo_rename_win'
    if mc.workspaceControl(f"{win_name}WorkspaceControl", query=True, exists=True):
        mc.workspaceControl(f"{win_name}WorkspaceControl", edit=True, close=True)
        mc.deleteUI(f"{win_name}WorkspaceControl", control=True)

    win = GizmoRenameUI()
    win.setObjectName(win_name)
    win.show()
    return win
