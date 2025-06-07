from gizmo.standalone import node_editor
from gizmo.maya.utils.widgets import *
import maya.cmds as mc


class MayaNodeEditor(GMainWindow, node_editor.core.NodeUI):
    def __init__(self):
        super().__init__()
        pass


def launch():
    """ Remove any existing windows and launch. """
    win_name = 'gizmo_joint_win'
    if mc.workspaceControl(f"{win_name}WorkspaceControl", query=True, exists=True):
        mc.workspaceControl(f"{win_name}WorkspaceControl", edit=True, close=True)
        mc.deleteUI(f"{win_name}WorkspaceControl", control=True)

    win = MayaNodeEditor()
    win.setObjectName(win_name)
    win.show()
    return win