import os
import maya.cmds as mc


def add_shelf():
    """Add Gizmo shelf to Maya.

    Check for an existing shelf, empty it and re-add the buttons or create a new one
    """
    shelf = 'gizmo'
    if mc.shelfLayout(shelf, ex=1):
        if mc.shelfLayout(shelf, q=1, ca=1):
            for each in mc.shelfLayout(shelf, q=1, ca=1):
                mc.deleteUI(each)
    else:
        shelf = mc.shelfLayout(shelf, p="ShelfLayout")
    mc.shelfButton(p=shelf,
                   width=37,
                   height=37,
                   style="iconAndTextVertical",
                   overlayLabelColor=(1, 1, 1),
                   overlayLabelBackColor=(0, 0, 0, 0),
                   imageOverlayLabel='R',
                   image=os.path.join(os.path.dirname(__file__), "media/gizmo-orange-icon.png"),
                   command='import gizmo\ngizmo.rename.launch()')
    print("Gizmo shelf loaded.")
