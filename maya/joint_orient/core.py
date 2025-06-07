"""Rename selected object's in Maya scene.

This script creates a UI that allows the user to edit an objects name. You can
add or remove digits from a name, as well as search and replace keywords. Or even
replace the name entirely.

The history is stored allowing you to easily undo all name changes.

# Todo: update orientations with skinning and bindpose intact:
"""
import logging
from maya.api import OpenMaya as om
import maya.cmds as mc
from .. import utils

log = logging.getLogger("Joint Orient")
log.setLevel(logging.DEBUG)


@utils.undo_chunk
def orient_to_world(joints, aim: tuple[int, int, int], up: tuple[int, int, int], axis: tuple[int, int, int] = (1, 0, 0)) -> None:
    """Orient selected joints to world."""
    if any(mc.objectType(jnt) != 'joint' for jnt in joints):
        raise ValueError('Joints expected, got unknown type.')

    # core.orient_to_world(sel)
    axis = om.MVector(*axis)
    for jnt in joints:
        children = mc.listRelatives(jnt, children=1, type='joint')
        if not children:
            mc.makeIdentity(jnt, apply=True, rotate=True, jointOrient=True)
            continue

        pos = om.MVector(mc.xform(jnt, query=1, worldSpace=1, translation=1)) + axis * 10
        utils.orient_joint(jnt, pos, forward_dir=aim, up_dir=up)


@utils.undo_chunk
def set_orient(joints: list[str], fwd_axis: tuple = (0, 0, 1), up_axis: tuple = (1, 0, 0)) -> None:
    """
    Orient joint so fwd_axis is pointing at the child with the up_axis perpendicular.

    Args:
        joints: joint chain to orient.
        fwd_axis: axis to aim at child.
        up_axis: axis to be perpendicular.

    """
    for x in joints:
        children = mc.listRelatives(x, children=True, type='joint')
        if not children:
            mc.makeIdentity(x, apply=True, rotate=True, jointOrient=True)
            continue

        for z in children:
            mc.parent(z, world=True)

        utils.orient_joint(x, children[0], forward_dir=fwd_axis, up_dir=up_axis)
        for z in children:
            mc.parent(z, x)


@utils.undo_chunk
def edit_orient(joints: list[str], add: bool = True, euler_value: list[int | float] = (0, 0, 0)) -> None:
    """
    Update joint orient for selected joints.

    Args:
        joints: joints to edit.
        add: if True add euler_value, else subtract.
        euler_value: x, y, x rotation values.

    """
    if any(mc.objectType(jnt) != 'joint' for jnt in joints):
        raise ValueError('Joints expected, got unknown type.')

    for x in joints:
        children = mc.listRelatives(x, children=1, type='joint')
        if not children:
            mc.makeIdentity(x, apply=True, rotate=True, jointOrient=True)
            continue

        for z in children:
            mc.parent(z, world=True)

        rotate = mc.xform(x, query=True, objectSpace=True, rotation=True)
        mc.setAttr(f"{x}.rotate", 0, 0, 0)

        utils.tweak_orient(x, euler_value, add=add)
        utils.zero_joint_orient(x)

        for z in children:
            mc.parent(z, x)

        mc.setAttr(f"{x}.rotate", *rotate)


@utils.undo_chunk
def reset_orient(joints: list[str]) -> None:
    """Orient selected joints to world."""

    if any(mc.objectType(jnt) != 'joint' for jnt in joints):
        raise ValueError('Joints expected, got unknown type.')

    for jnt in joints:
        children = mc.listRelatives(jnt, children=True, type='joint')
        if not children:
            mc.makeIdentity(jnt, apply=True, rotate=True, jointOrient=True)
            continue

        for z in children:
            mc.parent(z, world=True)

        utils.orient_joint(jnt)
        for z in children:
            mc.parent(z, jnt)


@utils.undo_chunk
def set_rot_order(joints: list[str], ro: int) -> None:
    """Update rotation order for selected joints."""

    if any(mc.objectType(jnt) != 'joint' for jnt in joints):
        raise ValueError('Joints expected, got unknown type.')

    for jnt in joints:
        mc.setAttr(f'{jnt}.rotateOrder', ro)


@utils.undo_chunk
def set_local_axis_vis(joints: list[str], value: bool):
    """ show/hide local axis on selected transform objects. """
    utils.set_local_axis_vis(joints, value)
