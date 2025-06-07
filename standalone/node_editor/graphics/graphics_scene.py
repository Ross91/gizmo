from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import math


class GraphicsScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super(GraphicsScene, self).__init__(*args, **kwargs)

        self.filepath = ''
        self.filename = ''
        self.rig = ''

        self.nodes = []
        self.edges = []
        self.graphics_scene = None

        # settings
        self.setSceneRect(QRect(10000, 10000, 10000, 10000))
        self.gris_size = 20
        self.grid_square = 5

        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)

        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)

    def drawBackground(self, painter, rect):
        super(GraphicsScene, self).drawBackground(painter, rect)

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.gris_size)
        first_top = top - (top % self.gris_size)

        lines_light = []
        lines_dark = []
        for x in range(first_left, right, self.gris_size):
            if x % (self.gris_size * self.grid_square) != 0:
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, self.gris_size):
            if y % (self.gris_size * self.grid_square) != 0:
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)

        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)

    def add_node(self, item):
        item.scene = self
        self.addItem(item)
        self.nodes.append(item)

    def delete_node(self, item):
        item.UserDeleted.emit(True)
        self.nodes.remove(item)
        self.removeItem(item)

    def add_edge(self, item):
        item.scene = self
        self.addItem(item)
        self.nodes.append(item)

    def delete_edge(self, item):
        self.nodes.remove(item)
        self.removeItem(item)


