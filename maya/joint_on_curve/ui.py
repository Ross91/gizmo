import logging
from PySide2.QtWidgets import *
import maya.cmds as mc
from ..utils.widgets import *
from .. import utils
from . import core

log = logging.getLogger("Joint on Curve")
log.setLevel(logging.DEBUG)


class JointOnCurveUI(GMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Joints on Curve")
        self.setFixedSize(250, 100)

        self.text_box = QLineEdit()
        self.curve_btn = QPushButton("<<<")
        self.combo_box = QComboBox()
        for i in range(2, 20):
            self.combo_box.addItem(str(i))

        self.create_btn = QPushButton("Create")

        # Layout for first row
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.text_box)
        row1_layout.addWidget(self.curve_btn)

        # Layout for second row
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(self.combo_box)
        row2_layout.addWidget(self.create_btn)

        # Main vertical layout
        wgt = QWidget()
        main_layout = QVBoxLayout()
        wgt.setLayout(main_layout)
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)
        self.curve_btn.clicked.connect(self.get_curve)
        self.create_btn.clicked.connect(self.do_place_joints)

        self.setCentralWidget(wgt)
        self.setLayout(main_layout)

    def get_curve(self):
        sel = mc.ls(sl=1)
        if not sel:
            return

        if core.check_sel_type(sel[0]):
            self.text_box.setText(sel[0])

    @utils.undo_chunk
    def do_place_joints(self):
        qty = int(self.combo_box.itemText(self.combo_box.currentIndex()))
        core.make_joints_on_curve(self.text_box.text(), qty)


def launch():
    """ Remove any existing windows and launch. """
    win_name = 'gizmo_jointOC_win'
    if mc.workspaceControl(f"{win_name}WorkspaceControl", query=True, exists=True):
        mc.workspaceControl(f"{win_name}WorkspaceControl", edit=True, close=True)
        mc.deleteUI(f"{win_name}WorkspaceControl", control=True)

    win = JointOnCurveUI()
    win.setObjectName(win_name)
    win.show()
    return win
