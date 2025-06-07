"""Reorient Selected Joints in Maya.

Compatible with Python 3.7.7
"""
import logging
from PySide2.QtWidgets import *
import maya.cmds as mc
from ..utils.widgets import *
from .. import utils
from . import core

log = logging.getLogger("Joint Orient")
log.setLevel(logging.DEBUG)


class JointOrientUI(GMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Joint Orient v1.0')
        self._aim_axis = (0, 1, 0)
        self._up_axis = (1, 0, 0)
        self._euler_value = (0, 0, 0)
        self._rotate_order = 0
        self._setup_ui()
        self.setFixedSize(275, 450)
        self.do_filter_child_events()

    def _setup_ui(self) -> None:

        # Central widget for QMainWindow
        central_widget = QWidget(self)
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(5, 5, 5, 5)
        central_widget.setLayout(main_lyt)
        self.setCentralWidget(central_widget)

        # Axis display
        display_grp = widgets.GroupBoxText('Local Rotation Axis')
        display_grp.setStatusTip("Toggle local axis display for selected.")
        display_lyt = QHBoxLayout()

        show_btn = QPushButton("Show")
        hide_btn = QPushButton("Hide")

        display_lyt.addWidget(show_btn)
        display_lyt.addWidget(hide_btn)
        display_grp.setLayout(display_lyt)

        main_lyt.addWidget(display_grp)

        # Orient selected
        orient_lyt = QVBoxLayout()
        orient_grp = widgets.GroupBoxText('Orient selected')
        orient_grp.setStatusTip("Aim joint at child.")
        orient_grp.setLayout(orient_lyt)

        aim_lyt = widgets.AxisLayout("Aim Axis", 1)
        aim_lyt.userEdit.connect(lambda x: setattr(self, '_aim_axis', x))

        up_lyt = widgets.AxisLayout(" Up Axis", 0)
        up_lyt.userEdit.connect(lambda x: setattr(self, '_up_axis', x))

        orient_btn = QPushButton("Go")
        orient_btn.setToolTip("Orient joint(s) to child using selected axis.")

        orient_world_btn = QPushButton("World")
        orient_world_btn.setToolTip("Orient joint(s) to world axis.")

        orient_grp.setLayout(orient_lyt)
        orient_lyt.addLayout(aim_lyt)
        orient_lyt.addLayout(up_lyt)
        orient_lyt.addWidget(orient_btn)
        orient_lyt.addWidget(orient_world_btn)

        main_lyt.addWidget(orient_grp)

        # Edit selected
        tweak_grp = widgets.GroupBoxText('Edit selected')
        tweak_grp.setStatusTip("Manually rotate joint(s).")
        tweak_lyt = QVBoxLayout()
        tweak_grp.setLayout(tweak_lyt)

        euler_lyt = widgets.EulerLayout()
        euler_lyt.userEdit.connect(lambda x: setattr(self, '_euler_value', x))
        tweak_lyt.addLayout(euler_lyt)

        tweak_button_lyt = QHBoxLayout()
        tweak_lyt.addLayout(tweak_button_lyt)

        add_btn = QPushButton("Add")

        sub_btn = QPushButton("Subtract")

        tweak_button_lyt.addWidget(add_btn)
        tweak_button_lyt.addWidget(sub_btn)

        rot_to_jo_btn = QPushButton("Zero Rotations")
        rot_to_jo_btn.setToolTip("Transfer rotations to joint orient.")
        tweak_lyt.addWidget(rot_to_jo_btn)

        tweak_sub_lyt = QHBoxLayout()
        tweak_lyt.addLayout(tweak_sub_lyt)

        align_x_btn = QPushButton("World X")
        align_x_btn.setToolTip("Align joint aim axis to world x-axis")

        align_y_btn = QPushButton("World Y")
        align_y_btn.setToolTip("Align joint aim axis to world y-axis")

        align_z_btn = QPushButton("World Z")
        align_z_btn.setToolTip("Align joint aim axis to world z-axis")

        tweak_sub_lyt.addWidget(align_x_btn)
        tweak_sub_lyt.addWidget(align_y_btn)
        tweak_sub_lyt.addWidget(align_z_btn)

        main_lyt.addWidget(tweak_grp)

        # Rotate Order
        ro_lyt = QHBoxLayout()
        ro_grp = widgets.GroupBoxText('Rotate Order')
        ro_grp.setStatusTip("Change rotate order for joint(s).")
        ro_grp.setLayout(ro_lyt)

        ro = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']
        ro_combo = QComboBox(self)
        ro_combo.addItems(ro)
        ro_combo.currentIndexChanged.connect(lambda x: setattr(self, '_rotate_order', x))
        ro_lyt.addWidget(ro_combo)

        ro_button = QPushButton("Set")
        ro_lyt.addWidget(ro_button)

        main_lyt.addWidget(ro_grp)
        main_lyt.addStretch(1)

        show_btn.clicked.connect(self._do_show_local_axis)
        hide_btn.clicked.connect(self._do_hide_local_axis)
        orient_btn.clicked.connect(self._do_orient_selected)
        orient_world_btn.clicked.connect(self._do_reset_selected)
        add_btn.clicked.connect(self._do_add_rotate)
        sub_btn.clicked.connect(self._do_subtract_rotate)
        rot_to_jo_btn.clicked.connect(self._do_clean_rotate)
        align_x_btn.clicked.connect(self._do_orient_to_world_x)
        align_y_btn.clicked.connect(self._do_orient_to_world_y)
        align_z_btn.clicked.connect(self._do_orient_to_world_z)
        ro_button.clicked.connect(self._do_set_rot_order)

    @staticmethod
    def _do_clean_rotate() -> None:
        """Transfer rotate values to joint orient"""
        utils.clean_rotation(_get_selected())

    def _do_orient_selected_to_world(self, axis: tuple[int, int, int] = (1, 0, 0)) -> None:
        """Orient selected joints to world."""
        sel = _get_selected()
        core.orient_to_world(sel, self._aim_axis, self._up_axis, axis)
        mc.select(sel)

    def _do_orient_to_world_x(self) -> None:
        """Aim selected joints along world x-axis."""
        sel = _get_selected()
        core.orient_to_world(sel, self._aim_axis, self._up_axis, (1, 0, 0))
        mc.select(sel)

    def _do_orient_to_world_y(self) -> None:
        """Aim selected joints along world y-axis."""
        sel = _get_selected()
        core.orient_to_world(sel, self._aim_axis, self._up_axis, (0, 1, 0))
        mc.select(sel)

    def _do_orient_to_world_z(self) -> None:
        """Aim selected joints along world z-axis."""
        sel = _get_selected()
        core.orient_to_world(sel, self._aim_axis, self._up_axis, (0, 0, 1))
        mc.select(sel)

    def _do_orient_selected(self) -> None:
        """Update joint orient on selected joints."""
        sel = _get_selected()
        core.set_orient(sel, self._aim_axis, self._up_axis)
        mc.select(sel)

    def _do_add_rotate(self) -> None:
        """Update rotation for selected joints."""
        sel = _get_selected()
        core.edit_orient(sel, True, list(self._euler_value))
        mc.select(sel)

    def _do_subtract_rotate(self) -> None:
        """Update rotation for selected joints."""
        sel = _get_selected()
        core.edit_orient(sel, False, list(self._euler_value))
        mc.select(sel)

    @staticmethod
    def _do_reset_selected() -> None:
        """Orient selected joints to world."""
        sel = _get_selected()
        core.reset_orient(sel)
        mc.select(sel)

    def _do_set_rot_order(self) -> None:
        """Update rotation order for selected joints."""
        sel = _get_selected()
        core.set_rot_order(sel, self._rotate_order)

    @staticmethod
    def _do_show_local_axis():
        sel = _get_selected()
        core.set_local_axis_vis(sel, True)

    @staticmethod
    def _do_hide_local_axis():
        sel = _get_selected()
        core.set_local_axis_vis(sel, False)


def _get_selected() -> list[str]:
    """Get selected joints."""
    sel = mc.ls(selection=1, type='joint') or []
    if not sel:
        RuntimeError("No joint(s) selected!")

    return sel


def launch():
    """ Remove any existing windows and launch. """
    win_name = 'gizmo_joint_win'
    if mc.workspaceControl(f"{win_name}WorkspaceControl", query=True, exists=True):
        mc.workspaceControl(f"{win_name}WorkspaceControl", edit=True, close=True)
        mc.deleteUI(f"{win_name}WorkspaceControl", control=True)

    win = JointOrientUI()
    win.setObjectName(win_name)
    win.show()
    return win