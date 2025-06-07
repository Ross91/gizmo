from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from .meta import MetaNode


class GraphicsSocket(QObject, QGraphicsItem, MetaNode):
    UserDeleted = Signal(bool)

    def __init__(self, node, name, socket_type=1):
        QObject.__init__(self)
        QGraphicsItem.__init__(self)
        MetaNode.__init__(self)

        self.node = node
        self.node.UserDeleted.connect(self._removed)
        self.setParentItem(node)
        self.setPos(name)

        self.radius = 6.0
        self.outline_width = 1.0
        self._colors = [
            QColor("#FFFF7700"),  # orange
            QColor("#FF52e220"),  # green (translate & rotate)
            QColor("#FF0056a6"),  # blue
            QColor("#FFa86db1"),  # purple
            QColor("#FFb54747"),  # dark red/orange
            QColor("#FFdbe220"),  # yellow
        ]
        self._color_background = self._colors[socket_type]
        self._color_outline = QColor("'FF000000")

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color_background)

    def _removed(self):
        self.UserDeleted.emit(True)

    def paint(self, painter, QStyleOptionGraphicsWidget, widget=None):
        # painter circle
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

    def boundingRect(self):
        return QRectF(
            -self.radius - self.outline_width,
            -self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width)
        )
