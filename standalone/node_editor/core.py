import sys
from PySide2.QtWidgets import *
from gizmo import constants as c
from .graphics.graphics_view import GraphicsView
from .graphics.graphics_scene import GraphicsScene
from .graphics.graphics_node import GraphicsNode


class NodeUI(QMainWindow):

    scene = None
    view = None
    nodes = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Node Editor')
        self.setFixedSize(1275, 750)
        _widget = QWidget(self)
        lyt = QHBoxLayout()
        _widget.setLayout(lyt)
        self.setCentralWidget(_widget)
        self.setContentsMargins(0, 0, 0, 0)
        with open(c.STYLE.DEFAULT, 'r') as f:
            self.setStyleSheet(f.read())

        self.scene = GraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.show()
        lyt.addWidget(self.view, stretch=2)

        self.scene.add_node(GraphicsNode('Default', self.scene, position=[500, 500], inputs=["x", "y"],  outputs=['Ross', "h"]))

        # menu = QWidget()
        # lyt.addWidget(menu, stretch=1)
        self.show()


def launch():

    win = NodeUI()
    win.show()
    return win

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NodeUI()
    window.show()
    sys.exit(app.exec_())