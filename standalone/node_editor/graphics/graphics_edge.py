from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import math
import socket

EDGE_CV_ROUNDNESS = 100

from shiboken2 import isValid

class GraphicsEdge(QGraphicsPathItem):
    def __init__(self, session, parent=None):
        super(GraphicsEdge, self).__init__(parent)

        self.edge = None
        self._color = QColor("#001000")
        self._selected_color = QColor("#00ff00")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._selected_color)
        self._pen_dragging = QPen(self._color)
        self._pen_dragging.setWidthF(2.0)
        self._pen_dragging.setStyle(Qt.DashDotLine)
        self._pen.setWidthF(2.0)
        self._pen_selected.setWidthF(2.0)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(2)

        self.start_parent = None
        self.end_parent = None
        self.start = [0, 0]
        self.end = [200, 100]
        self.is_live = False
        self.session = session

    def set_source(self, value, node=None):
        if node:
            node.UserDeleted.connect(self.remove)
            self.start_parent = node
        if isinstance(value, QPointF):
            self.start = value
        else:
            self.start = QPointF(value[0], value[1])

    def set_destination(self, value, node=None):
        if node:
            node.UserDeleted.connect(self.remove)
            self.end_parent = node
            self.is_live = True

        if isinstance(value, QPointF):
            self.end = value
        else:
            self.end = QPointF(value[0], value[1])

        self.update_path()

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        self.update_path()
        if self.edge is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen if not self.isSelected() else self._pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

    def update_path(self):
        # handle drawing QPainterPath form point A to B
        raise NotImplemented("This method has to be overwridden in a child class")

    def remove(self):
        # self.edge.remove()
        self.session.delete_edge(self)


class GraphicsEdgeDirect(GraphicsEdge):
    def update_path(self):
        start = self.start_parent.scenePos() if self.start_parent else self.start
        end = self.end_parent.scenePos() if self.end_parent else self.end
        path = QPainterPath(start)
        path.lineTo(end)
        self.setPath(path)


class GraphicsEdgeBezier(GraphicsEdge):
    def update_path(self):
        start = self.start_parent.scenePos() if self.start_parent is not None else self.start
        end = self.end_parent.scenePos() if self.end_parent is not None else self.end

        path = QPainterPath()
        ctrl1 = QPointF(start.x() + 100, start.y())
        ctrl2 = QPointF(end.x() - 100, end.y())

        path.moveTo(start)
        path.cubicTo(ctrl1, ctrl2, end)

        self.setPath(path)
