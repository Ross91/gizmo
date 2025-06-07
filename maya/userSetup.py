import maya.cmds as mc
import maya.mel as mel


def create_menu():
    if mc.menu("Gizmo", exists=True):
        mc.deleteUI("Gizmo")

    g_menu = mc.menu("Gizmo", label="Gizmo", parent=mel.eval("$retvalue = $gMainWindow;"))
    mc.menuItem(label="Connect to PyCharm", parent=g_menu, command='gizmo.standalone.pydebug.connect()')
    mc.menuItem(label="Rename", parent=g_menu, command='gizmo.maya.renamer.launch()')
    mc.menuItem(label="Joint Orient", parent=g_menu, command='gizmo.maya.joint_orient.launch()')
    mc.menuItem(label="Joints on Curve", parent=g_menu, command='gizmo.maya.joint_on_curve.launch()')
    mc.menuItem(label="Node Editor", parent=g_menu, command='gizmo.maya.maya_node_editor.launch()')

# mc.evalDeferred(create_menu)
