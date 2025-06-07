import maya.cmds as mc


def check_sel_type(obj):
    """Make sure we're dealing with a nurbsCurve"""
    shapes = mc.listRelatives(obj, shapes=True)
    if not shapes:
        return False

    if mc.nodeType(shapes[0]) == 'nurbsCurve':
        return True

    return False


def make_joints_on_curve(target: str | list[str], quantity: int) -> list[str]:
    """
    Place joints along nurbs curve spaced evenly.
    Args:
        target: NurbsCurve to place joints on.
        quantity: amount of joints required.

    Returns:
        list of joints in hierarchy order
    """
    if not isinstance(target, list):
        target = [target]

    spans = quantity - 1
    for x in target:
        crv = mc.duplicate(x, n=x + '_Temp')
        mc.rebuildCurve(crv, ch=False, rpo=True, end=True, kr=False, spans=spans)
        count = 0
        joints = []

        while count < quantity:
            ep = mc.select(crv[0] + '.ep[' + str(count) + ']')
            pos = mc.xform(ep, q=True, ws=True, t=True)
            mc.select(cl=1)
            jnt = mc.joint(p=pos)
            if joints:
                mc.parent(jnt, joints[-1])
            joints.append(jnt)
            count += 1

        mc.delete(crv)

