from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from .meta import MetaNode
from .graphics_socket import GraphicsSocket


class GraphicsNode(QObject, QGraphicsItem, MetaNode):
    UserDeleted = Signal(bool)

    width = 180.0
    height = 240.0
    padding = 4.0
    edge_size = 5.0
    text_height = 24.0
    name = ''

    def __init__(self, name, session, position=None, inputs: list = None, outputs: list = None, parent=None):
        QObject.__init__(self)
        QGraphicsItem.__init__(self)
        MetaNode.__init__(self)

        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        self.name = name
        self.session = session
        self._create()

        if position is None:
            position = [0.0, 0.0]

        self.setPos(QPointF(position[0], position[1]))

        self.inputs = []
        for i in inputs:
            self.add_socket(i)

        self.outputs = []
        for o in outputs:
            self.add_socket(o, False)

        self.setZValue(1)

    def _create(self):

        self._title_color = Qt.white
        self._title_font = QFont("Ubuntu", 11)

        self.pen_default = QPen(QColor("#7f000000"), 2)
        self.pen_selected = QPen(QColor("#FFFFA637"), 3)

        self._brush_title = QBrush(QColor("#6d6d6d"))
        self._brush_background = QBrush(QColor("#7e7e7e"))

        # create title
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(self.name)
        self.text_item.node = self.name
        self.text_item.setDefaultTextColor(self._title_color)
        self.text_item.setFont(self._title_font)
        self.text_item.setPos((self.width / 2) - QLabel().fontMetrics().boundingRect(self.name).width(), -22)
        self.text_item.setTextWidth(self.width - 2 * self.padding)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def add_socket(self, name, input=True):
        if input:
            offset = 30 + len(self.inputs) * 20
            socket = GraphicsSocket(self, QPointF(0.0, offset))
            self.inputs.append(socket)
        else:
            offset = 30 + len(self.outputs) * 20
            socket = GraphicsSocket(self, QPointF(self.width, offset))
            self.outputs.append(socket)

    def boundingRect(self):
        return QRectF(0, 0, 2 * self.edge_size + self.width, 2 * self.edge_size + self.height).normalized()

    def paint(self, painter, QstyleOptionGraphicsItem, widget=None):

        self.text_item.setDefaultTextColor(self._title_color if not self.isSelected() else QColor("#FFFFA637"))

        # content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundedRect(0,
                                    0,
                                    self.width,
                                    self.height,
                                    self.edge_size,
                                    self.edge_size)

        path_content.addRect(0, self.text_height, self.edge_size, self.edge_size)
        path_content.addRect(self.width - self.edge_size, self.text_height, self.edge_size, self.edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # title bar
        title = QPainterPath()
        title.setFillRule(Qt.WindingFill)
        title.addRoundedRect(0, 0, self.width, self.text_height, self.edge_size, self.edge_size)
        title.addRect(0, self.text_height - self.edge_size, self.edge_size, self.edge_size)
        title.addRect(self.width - self.edge_size,
                      self.text_height - self.edge_size,
                      self.edge_size, self.edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(title.simplified())

        # outline
        outline = QPainterPath()
        outline.addRoundedRect(0, 0, self.width, self.height, self.edge_size, self.edge_size)
        painter.setPen(self.pen_default if not self.isSelected() else self.pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(outline.simplified())
