from __future__ import annotations
import typing
import math

from maya.api import OpenMaya as om
import maya.cmds as mc
from .general import undo_chunk, get_m_transform


class KDTree:
    """
    Original implementation can be found here:
    https://github.com/Vectorized/Python-KD-Tree/blob/master/kd_tree.py

    A super short KD-Tree for points...
    so concise that you can copypasta into your homework
    without arousing suspicion.

    This implementation only supports Euclidean distance.

    The points can be any array-like type, e.g:
    lists, tuples, numpy arrays.

    Usage:
    1. Make the KD-Tree:
        `kd_tree = KDTree(points, dim)`
    2. You can then use `get_knn` for k nearest neighbors or
       `get_nearest` for the nearest neighbor

    points are be a list of points: [[0, 1, 2], [12.3, 4.5, 2.3], ...]
    """

    def __init__(
            self,
            points: list[tuple[float, float, float]],
            dim: int = 3,
            dist_sq_func: typing.Callable = None
    ) -> None:
        """Makes the KD-Tree for fast lookup.

        Args:
            points: A list of world space positions.
            dim: The dimension of the points(1D, 2D, 3D...)
            dist_sq_func : function(point, point), optional.
                A function that returns the squared Euclidean distance
                between the two points.
                If omitted, it uses the default implementation.
        """
        self.points = points
        self.ids = {v: i for i, v in enumerate(self.points)}

        if dist_sq_func is None:
            dist_sq_func = lambda a, b: sum((x - b[i]) ** 2
                                            for i, x in enumerate(a))

        def make(points, i=0):
            if len(points) > 1:
                points.sort(key=lambda x: x[i])
                i = (i + 1) % dim
                m = len(points) >> 1
                return [make(points[:m], i), make(points[m + 1:], i),
                        points[m]]
            if len(points) == 1:
                return [None, None, points[0]]

        def add_point(node, point, i=0):
            if node is not None:
                dx = node[2][i] - point[i]
                for j, c in ((0, dx >= 0), (1, dx < 0)):
                    if c and node[j] is None:
                        node[j] = [None, None, point]
                    elif c:
                        add_point(node[j], point, (i + 1) % dim)

        import heapq

        def get_knn(node, point, k, return_dist_sq, heap, i=0, tiebreaker=1):
            if node is not None:
                dist_sq = dist_sq_func(point, node[2])
                dx = node[2][i] - point[i]
                if len(heap) < k:
                    heapq.heappush(heap, (-dist_sq, tiebreaker, node[2]))
                elif dist_sq < -heap[0][0]:
                    heapq.heappushpop(heap, (-dist_sq, tiebreaker, node[2]))
                i = (i + 1) % dim
                # Goes into the left branch, then the right branch if needed
                for b in (dx < 0, dx >= 0)[:1 + (dx * dx < -heap[0][0])]:
                    get_knn(node[b], point, k, return_dist_sq,
                            heap, i, (tiebreaker << 1) | b)
            if tiebreaker == 1:
                return [(-h[0], h[2]) if return_dist_sq else h[2]
                        for h in sorted(heap)][::-1]

        def walk(node):
            if node is not None:
                for j in 0, 1:
                    for x in walk(node[j]):
                        yield x
                yield node[2]

        self._add_point = add_point
        self._get_knn = get_knn
        self._root = make(self.points)
        self._walk = walk

    def __iter__(self):
        return self._walk(self._root)

    def add_point(self, point: list[float]):
        """Adds a point to the kd-tree.

        Args:
            point: co-ordinate position
        """
        if self._root is None:
            self._root = [None, None, point]
        else:
            self._add_point(self._root, point)

    def get_knn(self, point, k, return_dist_sq=True):
        """Returns k nearest neighbors.

        Parameters
        ----------
        point : array-like
            The point.
        k: int
            The number of nearest neighbors.
        return_dist_sq : boolean
            Whether to return the squared Euclidean distances.

        Returns
        -------
        list<array-like>
            The nearest neighbors.
            If `return_dist_sq` is true, the return will be:

                [(dist_sq, point), ...]
            else:
                [point, ...]
        """
        return self._get_knn(self._root, point, k, return_dist_sq, [])

    def get_nearest(self, point, return_dist_sq=True):
        """Returns the nearest neighbor.

        Parameters
        ----------
        point : array-like
            The point.
        return_dist_sq : boolean
            Whether to return the squared Euclidean distance.

        Returns
        -------
        array-like
            The nearest neighbor.
            If the tree is empty, returns `None`.
            If `return_dist_sq` is true, the return will be:
                (dist_sq, point)
            else:
                point
        """
        l = self._get_knn(self._root, point, 1, return_dist_sq, [])
        return l[0] if len(l) else None

    def union(self, obj):
        print("Getting union...")
        point_pair_ids = []

        for k, v in obj.ids.items():
            p = self.get_nearest(k)
            this_id = self.ids[p[1]]
            point_pair_ids.append((this_id, v))
        print("...Union finished.")
        return point_pair_ids


def orient_joint(
        jnt: str,
        target: (str, om.MVector) = None,
        forward_dir: tuple = (0, 0, 1),
        up_dir: tuple = (1, 0, 0)
) -> None:
    """ test

    Args:
        jnt: Name of joint to orient.
        target: object or world space vector to aim at.
        forward_dir: axis pointing towards the child/target object.
        up_dir: axis perpendicular to forward axis.
    Todo:
        check up axis
    """
    if forward_dir == up_dir:
        mc.warning("forward and up direction can't be the same")
        return
    up_dir = om.MVector(up_dir)
    forward_dir = om.MVector(forward_dir)

    # check if user want's direction reversed.
    # if so, do this later.
    negative_fwd = False
    negative_up = False
    negative_dirs = [om.MVector.kXnegAxisVector, om.MVector.kYnegAxisVector, om.MVector.kZnegAxisVector]
    if any(forward_dir == x for x in negative_dirs):
        negative_fwd = True
        forward_dir = -forward_dir
    if any(up_dir == x for x in negative_dirs):
        negative_up = True
        up_dir = -up_dir

    # find forward vector.
    jnt_trans = get_m_transform(jnt)
    if target:
        if isinstance(target, om.MVector):
            target_t = target
        else:
            target_t = om.MVector(mc.xform(target, q=1, ws=1, t=1))

        jnt_pos = -jnt_trans.translation(om.MSpace.kWorld)
        forward_axis = target_t + jnt_pos
        forward_axis.normalize()
    else:
        forward_axis = om.MVector(forward_dir)

    # find up vector.
    # if forward vec is too close to world Y, use world Z.
    if abs(forward_axis * om.MVector.kYaxisVector) >= 0.9:
        up_axis = forward_axis ^ om.MVector.kYaxisVector
    else:
        up_axis = om.MVector.kYaxisVector ^ forward_axis

    # find last vector.
    other_axis = forward_axis ^ up_axis

    # create matrix from directional vectors.
    mtx = om.MTransformationMatrix(sort_matrix(forward_dir,
                                               up_dir,
                                               forward_axis,
                                               up_axis,
                                               other_axis))
    mtx.setScale((1, 1, 1), om.MSpace.kWorld)
    mtx.setTranslation(jnt_trans.translation(om.MSpace.kWorld), om.MSpace.kWorld)

    # reverse directions by rotating 180 degrees.
    if negative_fwd:
        mtx.rotateBy(om.MQuaternion(3.14, up_axis), om.MSpace.kWorld)
    if negative_up:
        fwd = forward_dir * mtx.asMatrix()
        mtx.rotateBy(om.MQuaternion(3.14, fwd), om.MSpace.kWorld)

    # set joint rotation and transfer values to joint orient.
    # so rotate values are zeroed.
    # apply with xform, otherwise ctrl+Z won't work.
    mc.xform(jnt, ws=1, m=list(mtx.asMatrix()))
    mc.makeIdentity(jnt, a=True, r=True)


def sort_matrix(
        fwd_axis: list[float],
        up_axis: list[float],
        fwd_vec: list[float],
        up_vec: list[float],
        other_vec: list[float]
) -> om.MMatrix:
    """Sort directional vectors into correct matrix order.

    Args:
        fwd_axis: forward axis for matrix.
        up_axis: up axis for matrix.
        fwd_vec: vector position.
        up_vec: vector position.
        other_vec: vector position.

    Returns:
        composed matrix.
    """

    def set_element(_matrix, row, values):
        for i, v in enumerate(list(values)):
            _matrix.setElement(row, i, v)
        return _matrix

    matrix = om.MMatrix()
    if fwd_axis == om.MVector.kXaxisVector:
        matrix = set_element(matrix, 0, fwd_vec)
        if up_axis == om.MVector.kYaxisVector:
            matrix = set_element(matrix, 1, up_vec)
            matrix = set_element(matrix, 2, other_vec)
        else:
            other_vec = -other_vec
            matrix = set_element(matrix, 1, other_vec)
            matrix = set_element(matrix, 2, up_vec)

    elif fwd_axis == om.MVector.kYaxisVector:
        matrix = set_element(matrix, 1, fwd_vec)
        if up_axis == om.MVector.kXaxisVector:
            matrix = set_element(matrix, 0, up_vec)
            matrix = set_element(matrix, 2, other_vec)
        else:
            matrix = set_element(matrix, 0, other_vec)
            matrix = set_element(matrix, 2, up_vec)
    else:
        matrix = set_element(matrix, 2, fwd_vec)
        if up_axis == om.MVector.kXaxisVector:
            matrix = set_element(matrix, 0, up_vec)
            matrix = set_element(matrix, 1, other_vec)
        else:
            other_vec = -other_vec
            matrix = set_element(matrix, 0, other_vec)
            matrix = set_element(matrix, 1, up_vec)

    return matrix


@undo_chunk
def tweak_orient(
        target: str,
        values: list[float],
        add: bool = True
) -> None:
    """Apply rotation value in object space.

    Args:
        target: Object to update rotation.
        values: Euler rotation values.
        add: Add or subtract the rotation value.
    """
    mtx = om.MTransformationMatrix(om.MMatrix(mc.xform(target, query=1, worldSpace=1, matrix=True)))
    if not add:
        values = [v * -1 for v in values]

    bpm = om.MTransformationMatrix(om.MMatrix(mc.getAttr(f'{target}.worldMatrix')))
    rot = om.MEulerRotation(math.radians(values[0]), math.radians(values[1]), math.radians(values[2]))
    mtx.rotateBy(rot, om.MSpace.kObject)
    bpm.rotateBy(rot, om.MSpace.kObject)
    mc.xform(target, worldSpace=True, matrix=list(mtx.asMatrix()))
    mc.setAttr(target + '.bindPose', list(bpm.asMatrix()), type='matrix')


def zero_joint_orient(child):
    parent = mc.listRelatives(child, p=True)[0]
    child_ws_matrix = om.MMatrix(mc.xform(child, q=True, ws=True, m=True))
    parent_ws_matrix = om.MMatrix(mc.xform(parent, q=True, ws=True, m=True))

    child_local_matrix = child_ws_matrix * parent_ws_matrix.inverse()
    child_local_transform_matrix = om.MTransformationMatrix(child_local_matrix)
    rotation = [math.degrees(rad) for rad in child_local_transform_matrix.rotation().asVector()]

    mc.setAttr(f"{child}.r", 0, 0, 0)
    mc.setAttr(f"{child}.jo", rotation[0], rotation[1], rotation[2])


def project_point(source: str,
                  target: str,
                  local_distance: float | int,
                  axis: str | tuple,
                  x_angle = tuple[int, int],
                  y_angle = tuple[int, int],
                  z_angle = tuple[int, int],
                  angle: tuple[tuple[int, int]] = ((0, 0), (0, 0))):
    """

    Args:
        source: source plane to project onto.
        target: joint to move
        local_distance: distance to be maintained between parent and child.
        angle: rotation limits
        axis: source joint forward axis, vector to create 2d plane for.

    Returns:
    """
    if isinstance(axis, str):
        if axis is 'x':
            n = om.MVector(list(om.MMatrix(mc.xform(target, q=1, ws=1, m=1)))[0:4]).normal()
        elif axis is 'y':
            n = om.MVector(list(om.MMatrix(mc.xform(target, q=1, ws=1, m=1)))[4:7]).normal()
        else:
            n = om.MVector(list(om.MMatrix(mc.xform(target, q=1, ws=1, m=1)))[7:10]).normal()
    else:
        n = om.MVector(axis).normal()

    p = om.MVector(mc.xform(target, q=1, ws=1, t=1))
    t = om.MVector(mc.xform(source, q=1, ws=1, t=1))
    orig = t + (n * -1) * local_distance
    v = p - orig
    # n = om.MVector(list(om.MMatrix(mc.xform(source, q=1, ws=1, m=1)))[4:7]).normal()
    dist = v * n
    proj = p - dist * n

    x_adj_len = []
    if x_angle:
        local_distance * math.tan(math.radians(x_angle[0]))
        local_distance * math.tan(math.radians(x_angle[1]))
        x_adj_len = local_distance * math.tan(math.radians(angle))
    adjacent_length = local_distance * math.tan(math.radians(angle))

    return orig + (proj + (orig * -1)).normal() * adjacent_length
