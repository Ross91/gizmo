
class MetaNode:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = None
        self.session = None
        self._pos = [0.0, 0.0]

    @property
    def x(self):
        return self._pos[0]

    @x.setter
    def x(self, value: float):
        self._pos[0] = value

    @property
    def y(self):
        return self._pos[1]

    @y.setter
    def y(self, value: float):
        self._pos[1] = value

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: list[float, float]):
        self._pos = value

    def register(self, *args, **kwargs):
        raise NotImplementedError

    def deregister(self, *args, **kwargs):
        raise NotImplementedError

    def serialise(self):
        raise NotImplementedError

    def deserialise(self):
        raise NotImplementedError


class MetaScene:
    def __init__(self):
        super(MetaScene, self).__init__()
        self.id = id(self)
        self.filename = 'temp.json'
        self.filepath = "D:/Ross/Documents/script_tools/NodeEditor/graphs//"

        self.scene_name = None
        self.scene_width = 64000
        self.scene_height = 64000

        self.nodes = []
        self.edges = []
        self.scene_data = None