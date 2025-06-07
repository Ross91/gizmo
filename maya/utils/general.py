"""Shared utility functions

General purpose functions to be shared across the codebase.
"""
import functools
import re
from maya.api import OpenMaya as om
import maya.cmds as mc
from maya import mel


def get_m_dagpath(obj: str) -> om.MDagPath:
    sel = om.MSelectionList()
    sel.add(obj)
    return sel.getDagPath(0)


def get_m_mesh(obj: str) -> om.MFnMesh:
    return om.MFnMesh(get_m_dagpath(obj))


def get_m_object(obj: str) -> om.MObject:
    sel = om.MSelectionList()
    sel.add(obj)
    return sel.getDependNode(0)


def get_m_transform(obj: str) -> om.MFnTransform:
    """Get OpenMaya transform object.

    Args:
        obj: name of scene object.
    """
    return om.MFnTransform(get_m_dagpath(obj))


def undo_chunk(func):
    """decorator function

    A single undo(ctrl+z) command in Maya will contain everything this decorator function has wrapped.
    So it's easy to undo code changes in the scene.
    """

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        mc.undoInfo(openChunk=True)
        try:
            return func(*args, **kwargs)
        finally:
            mc.undoInfo(closeChunk=True)

    return wrap


class UndoChunk:
    def __init__(self, name="customChunk"):
        self.name = name

    def __enter__(self):
        print("undo chunk start...")
        mc.undoInfo(openChunk=True, chunkName=self.name, infinity=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(closeChunk=True)
        print("...undo chunk end.")


class ProgressBar:
    def __init__(self, max_value, status):
        super().__init__()
        self._cancel = False
        self._count = 0
        self._max_count = max_value
        self._progress = mel.eval('$tmp = $gMainProgressBar')
        mc.progressBar(self._progress,
                       edit=True,
                       beginProgress=True,
                       isInterruptable=True,
                       status=status,
                       maxValue=max_value)

    @property
    def cancel(self):
        return self._cancel

    @cancel.setter
    def cancel(self, value):
        self._cancel = value

    def next(self):
        if self._cancel or self._count >= self._max_count:
            self.stop()

        mc.progressBar(self._progress, edit=True, step=1)
        self._count += 1

        if mc.progressBar(self._progress, query=True, isCancelled=True):
            self._cancel = True

    def stop(self):
        mc.progressBar(self._progress, edit=True, endProgress=True)

    def __del__(self):
        self.stop()


def split_string(name: str) -> list[str, str, str]:
    parts = name.split('_')
    if not len(parts) == 3:
        raise RuntimeError(f"failed to split {name} into (type, name, index), got: {parts}")
    return parts


def increment_string(x: str, i: int, padding: int = 2) -> str:
    """Sanity check, if name exists then increment until unique name found."""
    if not mc.objExists(x):
        return x

    pattern = re.compile(r'\d+$')
    match = pattern.search(x)
    if match:
        original = match.group(0)
        _index = int(original) + 1
        new_str = x[:len(original) * -1]
        if not new_str.endswith('_'):
            new_str += '_'
        new_str += str(_index).zfill(padding)
        return increment_string(new_str, i, padding)

    n = x
    if not n.endswith('_'):
        n += '_'
    n += str(i).zfill(padding)

    return increment_string(n, i, padding)


@undo_chunk
def rename_string(
        obj: str,
        name: str = '',
        prefix: str = '',
        suffix: str = '',
        remove_start=None,
        remove_end=None,
        search_replace: list[tuple[str]] = None,
        index: int = 1,
        number_padding: int = 2
        ) -> str:
    """ Rename selected object in scene.

    Args:
        obj: target object.
        name: replace existing name with this one.
        prefix: add text at the beginning.
        suffix: add test at the end.
        remove_start: remove x amount of digit from the beginning.
        remove_end: remove x amount of digits from the end.
        search_replace: search and replace keywords, each tuple is a separate check.
        index: Optional suffix.
        number_padding: padding for index. eg 2 = 01, 3 = 001.

    Returns:
        new name after user changes.
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

    obj = increment_string(obj, index, number_padding)

    return obj


def set_local_axis_vis(objs: list[str], visibility: bool):
    """Show local rotation axis for objects.

        Args:
            objs: list of transforms.
            visibility: show/hide.
        """
    for obj in objs:
        if not mc.objExists(obj):
            print("Warning -> Object doesn't exist")
            continue
        if not mc.attributeQuery('displayLocalAxis', node=obj, exists=True):
            print(f"{obj} has no displayLocalAxis attr!")
            continue
        mc.setAttr(obj + '.displayLocalAxis', visibility)


@undo_chunk
def clean_rotation(objs: list[str]) -> None:
    """Transfer rotation to joint orient.

    Args:
        objs: list of transforms.
    """
    for obj in objs:
        if not mc.objExists(obj):
            print("Warning -> Object doesn't exist")
            continue
        mc.makeIdentity(obj, apply=True, rotate=True)
