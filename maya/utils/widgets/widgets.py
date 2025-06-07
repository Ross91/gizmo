"""
Custom widgets.
A sub package of utils, to avoid polluting other modules with Pyside2.
I can control what functions are exposed to the user.
"""
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from ... import constants as c


class SearchReplaceLayout(QtWidgets.QVBoxLayout):
    """Custom class to group QCheckBox and multiple QLineEdit.

    Added custom Signal to help de-clutter main UI.
    """

    userEnabled = QtCore.Signal(bool)
    userEdit = QtCore.Signal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self._user_enabled = False

        search_layout = QtWidgets.QHBoxLayout()
        search_label = QtWidgets.QLabel('Search')
        search_label.setMinimumWidth(40)
        self.search_text = QtWidgets.QLineEdit()
        self.search_text.setEnabled(False)
        search_check = QtWidgets.QCheckBox()
        search_check.stateChanged.connect(
            lambda x: setattr(self, 'user_enabled', x)
        )
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_text)
        search_layout.addWidget(search_check)
        search_layout.addStretch(1)
        self.addLayout(search_layout)

        replace_layout = QtWidgets.QHBoxLayout()
        replace_label = QtWidgets.QLabel('Replace')
        replace_label.setMinimumWidth(40)
        self.replace_text = QtWidgets.QLineEdit()
        self.replace_text.setEnabled(False)
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_text)
        replace_layout.addStretch(1)

        self.search_text.textChanged.connect(
            lambda x: self.create_keyword_pairs(x, self.replace_text.text())
        )
        self.replace_text.textChanged.connect(
            lambda x: self.create_keyword_pairs(self.search_text.text(), x)
        )

        self.addLayout(replace_layout)

    @property
    def user_enabled(self) -> bool:
        """State"""
        return self._user_enabled

    @user_enabled.setter
    def user_enabled(self, value: bool):
        self._user_enabled = value
        self.replace_text.setEnabled(value)
        self.search_text.setEnabled(value)
        self.userEnabled.emit(value)

    def create_keyword_pairs(self, search_text: str, replace_text: str):
        """Emit a list of tuples.

        Filter text and pair keywords from search
        and replace text fields.
        """
        search_terms = search_text.replace(" ", "").split(',')
        replace_terms = replace_text.replace(" ", "").split(',')
        self.userEdit.emit([pair for pair in zip(search_terms, replace_terms)])


class SpinBoxLayout(QtWidgets.QHBoxLayout):
    """Custom class to group QCheckBox and QSpinBox.

    Added custom Signal to help de-clutter main UI.
    """

    userEnabled = QtCore.Signal(bool)
    userEdit = QtCore.Signal(int)

    def __init__(self, label='', enabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self._user_enabled = enabled
        self.setContentsMargins(2, 2, 2, 2)
        s_label = QtWidgets.QLabel(label)
        s_label.setMinimumWidth(25)
        self.spin_box = QtWidgets.QSpinBox()
        self.spin_box.setEnabled(enabled)
        self.spin_box.textChanged.connect(
            lambda x: self.userEdit.emit(int(x))
        )
        _label = QtWidgets.QLabel("Digit(s)")
        s_check = QtWidgets.QCheckBox()
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
    def user_enabled(self, value: bool):
        self._user_enabled = value
        self.spin_box.setEnabled(value)
        self.userEnabled.emit(value)


class EulerLayout(QtWidgets.QHBoxLayout):

    userEdit = QtCore.Signal(tuple)

    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        label_x = QtWidgets.QLabel('X:')
        self.x_axis = QtWidgets.QSpinBox()
        label_y = QtWidgets.QLabel('Y:')
        self.y_axis = QtWidgets.QSpinBox()
        self.z_axis = QtWidgets.QSpinBox()
        label_z = QtWidgets.QLabel('Z:')
        for axis in [self.x_axis, self.y_axis, self.z_axis]:
            axis.setRange(0, 360)
            axis.valueChanged.connect(self.set_value)

        self.addStretch(1)
        self.addWidget(label_x)
        self.addWidget(self.x_axis)
        self.addWidget(label_y)
        self.addWidget(self.y_axis)
        self.addWidget(label_z)
        self.addWidget(self.z_axis)
        self.addStretch(1)

    def set_value(self):
        self.userEdit.emit((self.x_axis.value(), self.y_axis.value(), self.z_axis.value()))


class AxisLayout(QtWidgets.QHBoxLayout):

    userEdit = QtCore.Signal(tuple)

    def __init__(self, label, default_value=0):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.orient_grp2 = QtWidgets.QButtonGroup(self)

        up_label = QtWidgets.QLabel(label + ': ')
        up_x = QtWidgets.QRadioButton('X')
        self.orient_grp2.addButton(up_x)
        self.orient_grp2.setId(up_x, 0)
        up_y = QtWidgets.QRadioButton('Y')
        self.orient_grp2.addButton(up_y)
        self.orient_grp2.setId(up_y, 1)
        up_z = QtWidgets.QRadioButton('Z')
        self.orient_grp2.addButton(up_z)
        self.orient_grp2.setId(up_z, 2)
        self.reverse = QtWidgets.QCheckBox('Reverse')

        self.orient_grp2.button(default_value).setChecked(True)

        self.reverse.toggled.connect(self.get_axis)
        self.orient_grp2.buttonClicked.connect(self.get_axis)

        self.addStretch(1)
        self.addWidget(up_label)
        self.addWidget(up_x)
        self.addWidget(up_y)
        self.addWidget(up_z)
        self.addWidget(self.reverse)
        self.addStretch(1)

    def get_axis(self):

        reverse = -1 if self.reverse.isChecked() else 1
        index = self.orient_grp2.checkedId()
        axis = [1, 0, 0]
        if index == 0:
            axis = [1, 0, 0]

        if index == 1:
            axis = [0, 1, 0]

        if index == 2:
            axis = [0, 0, 1]

        self.userEdit.emit([a * reverse for a in axis])


class GroupBoxText(QtWidgets.QGroupBox):
    """Custom QGroupBox to handle events and stylesheets"""

    message = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = False
        self.setMouseTracking(True)
        self.set_style(False)
        self.setContentsMargins(0, 0, 0, 0)

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
        """"""
        self.message.emit(self.statusTip())
        return super().enterEvent(event)


class GMainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.showMessage("opened")
        self.setStatusBar(self.status_bar)
        self.last_message = ''
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowIcon(QtGui.QIcon("C:/Dev/python/internal/maya/gizmo/source/media/gizmo.png"))


        # Todo: Turn of docking!
        with open(c.STYLE.DEFAULT, 'r') as f:
            self.setStyleSheet(f.read())

    def eventFilter(self, widget: QtCore.QObject, event: QtCore.QEvent):
        """Display tool tip info on status bar for user."""
        if event.type() == QtCore.QEvent.Enter:
            if hasattr(widget, 'statusTip') and widget.statusTip():
                self.status_bar.showMessage(widget.statusTip())
            if hasattr(widget, 'toolTip') and widget.toolTip():
                self.status_bar.showMessage(widget.toolTip())

        if event.type() == QtCore.QEvent.Leave:
            self.status_bar.showMessage(self.last_message)

        return super().eventFilter(widget, event)

    def do_filter_child_events(self) -> None:
        """Add event filter to all child widgets with tooltips."""

        children = self.findChildren(QtCore.QObject, '')
        for wgt in children:
            if hasattr(wgt, 'toolTip') and wgt.toolTip():
                wgt.installEventFilter(self)
                continue
            elif hasattr(wgt, 'statusTip') and wgt.statusTip():
                wgt.installEventFilter(self)
                continue
            else:
                continue


class GProgressDialog(MayaQWidgetDockableMixin, QtWidgets.QProgressDialog):
    def __init__(self, num_files, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum = 0
        self.setMaximum = num_files



