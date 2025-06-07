from __future__ import annotations
import logging

INFO_FORMAT = "[Gizmo][%(module)s] %(message)s"
DEBUG_FORMAT = "[Gizmo][%(levelname)s] %(message)s"
WARNING_FORMAT = "[Gizmo][%(levelname)s][%(funcName)s][%(lineno)d] %(message)s"


class GizmoFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        pass


class GizmoLogger(logging.getLoggerClass()):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

