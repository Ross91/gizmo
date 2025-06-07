
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from .graphics_node import GraphicsNode
from .graphics_edge import GraphicsEdgeDirect, GraphicsEdgeBezier
from .graphics_socket import GraphicsSocket


class GraphicsView(QGraphicsView):

    is_drawing_line = False
    is_dragging = False
    selected = None
    socket = None
    line_drag = None
    drag_start = None
    drag_end = None

    def __init__(self, scene):
        super(GraphicsView, self).__init__(scene)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.HighQualityAntialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.zoom_in_factor = 1.25
        self.zoom = 10
        self.zoom_step = 1
        self.zoom_range = [0, 10]
        self.mouse_in_view = False
        self.session = scene

    def wheelEvent(self, event):

        # calculate zoom factor
        zoom_out_factor = 1 / self.zoom_in_factor

        # calculate zoom
        if event.angleDelta().y() > 0:
            zoom_factor = self.zoom_in_factor
            self.zoom += self.zoom_step
        else:
            zoom_factor = zoom_out_factor
            self.zoom -= self.zoom_step

        clamp = False
        if self.zoom < self.zoom_range[0]:
            self.zoom = self.zoom_range[0]
            clamp = True
        if self.zoom > self.zoom_range[1]:
            self.zoom = self.zoom_range[1]
            clamp = True

        if not clamp:
            self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):

        # get widget under cursor
        item = self._get_event_item(event)

        # move around the scene by using the middle mouse button
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.is_dragging = True
            # faking a left button click as that's what GraphicsView expects
            press_event = QMouseEvent(
                event.Type(),
                event.localPos(),
                event.screenPos(),
                Qt.LeftButton,
                event.buttons() | Qt.LeftButton,
                event.modifiers()
            )
            self.mousePressEvent(press_event)
            return

        # create a line if we've clicked on a socket
        if event.button() == Qt.LeftButton and not self.is_dragging:

            if isinstance(item, GraphicsSocket):
                self.socket = item
                self.is_drawing_line = True
                self.line_drag = GraphicsEdgeBezier(self.session)
                self.line_drag.set_source(item.scenePos(), item)
                self.session.add_edge(self.line_drag)

                return

        super(GraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):

        # update lines if drawing any
        if self.is_drawing_line:
            p = self._map_to_scene(event.pos())
            offset = QPointF(p.x() - 10, p.y() - 10)
            self.line_drag.set_destination(offset)
            return

        super(GraphicsView, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):

        # delete selected nodes
        if event.key() == Qt.Key.Key_Delete:
            items = self.session.selectedItems()
            for i in items:
                self.session.delete_node(i)
            return

        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):

        # get widget under cursor
        item = self._get_event_item(event)

        # start creating a new line
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.is_dragging = False
            return

        # check for socket under cursor and connect, else delete.
        if event.button() == Qt.LeftButton and self.is_drawing_line:
            if isinstance(item, GraphicsSocket):
                self.is_drawing_line = False
                self.line_drag.set_destination(item.scenePos(), item)
                self.line_drag = None
                return

            self.session.delete_edge(self.line_drag)
            self.is_drawing_line = False
            self.line_drag = None
            return

        super(GraphicsView, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QEvent) -> None:

        # create node when user double clicks
        if event.button() == Qt.LeftButton:
            tt = self._map_to_scene(event.pos())
            self.session.add_node(GraphicsNode('Example',
                                               self.session,
                                               position=[tt.x(), tt.y()],
                                               inputs=['1', '2', '3'],
                                               outputs=['1', '2', '3']))
            return

        super(GraphicsView, self).mouseDoubleClickEvent(event)

    def _map_to_scene(self, pos: QPointF) -> QPointF:
        """Map position to QGraphicsView widget"""
        gp = self.mapToGlobal(pos)  # relative to screen
        rw = self.window().mapFromGlobal(gp)  # relative to window
        return self.mapToScene(rw)  # relative to GraphicsView

    def _get_event_item(self, event: QEvent) -> QPoint:
        """Get widget under mouse cursor"""
        pos = event.pos()
        obj = self.itemAt(pos)
        return obj
