"""Shared utility functions

General purpose functions to be shared across the codebase.
"""
import functools

import maya.cmds as mc


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
