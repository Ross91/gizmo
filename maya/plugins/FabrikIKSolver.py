"""
FABRIK: A fast, iterative solver for the Inverse Kinematics problem.
by Andreas Aristidou & Joan Lasenby.

Python implementation by Ross Harrop.

"""
from __future__ import annotations
from collections import Counter

import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.OpenMayaMPx as omx
import maya.cmds as mc
import sys

kPluginNodeTypeName = "ikFsolver"
fabrikNodeId = om.MTypeId(0x80100)


def _get_dag_path(name: str) -> om.MDagPath:
    sel = om.MSelectionList()
    sel.add(name)
    dag = om.MDagPath()
    sel.getDagPath(0, dag)
    return dag


class Node:
    """ Wrapper class for joints for ease of use with OpenMaya. """

    dag_path = None
    """: associated dag path for object."""

    transform = None
    """: associated MFnTransform for object"""

    name = None
    """: long name for joint."""

    def __init__(self, name: om.MDagPath):
        self.name = name.fullPathName()
        self.dag_path = name
        self.transform = om.MFnTransform(self.dag_path)

    @property
    def translation(self, space: om.MSpace = om.MSpace.kWorld) -> om.MVector:
        return self.transform.getTranslation(space)

    @translation.setter
    def translation(self, pos: om.MVector, space: om.MSpace = om.MSpace.kWorld):
        self.transform.setTranslation(pos, space)

    @property
    def rotation(self, space: om.MSpace = om.MSpace.kWorld) -> om.MEulerRotation:
        return self.transform.getRotation(space)

    @rotation.setter
    def rotation(self, rot: om.MEulerRotation | om.MQuaternion, space: om.MSpace = om.MSpace.kWorld):
        self.transform.setRotation(rot)


class NodeChain:
    """ Wrapper class to help organise and interact with joint chains. """

    ik_handle = None
    ": IK handle controlling the joint chain"

    nodes = None
    ": the joint chain"

    links = None
    ": list of distances between joints"

    isSub = False
    ": sub-chains are intermediary joints chains so FABRIC is solved in order."

    def __init__(self, n: list[str], ik: oma.MFnIkHandle = None):

        self.ik_handle = om.MVector(ik.getTranslation(om.MSpace.kWorld)) if ik else None
        self.nodes = []
        for x in n:
            t = Node(self._get_dag_path(x))
            t.sub = False
            self.nodes.append(t)

        self.links = []
        for i, node in enumerate(self.nodes[1:]):
            a = self.nodes[i].translation
            b = node.translation
            self.links.append((a - b).length())

    @property
    def root(self) -> Node:
        """ First joint in chain. """
        return self.nodes[0]

    @staticmethod
    def _get_dag_path(name: str) -> om.MDagPath:
        sel = om.MSelectionList()
        sel.add(name)
        dag = om.MDagPath()
        sel.getDagPath(0, dag)
        return dag


class FabrikIKSolver(omx.MPxIkSolverNode):
    """Custom IK Solver plugin with FABRIC"""

    ik_chains = []
    ": joints organised into NodeChain instances."

    sub_nodes = {}
    ": ik chains with the same joints"

    ik_handles = {}
    ": ik handles created by user"

    def __init__(self):
        omx.MPxIkSolverNode.__init__(self)

    @staticmethod
    def create():
        f = FabrikIKSolver()
        return omx.asMPxPtr(f)

    @staticmethod
    def initalize():
        return True

    def solverTypeName(self):
        return kPluginNodeTypeName

    @staticmethod
    def _sort_joint_chains(l_jnts):

        flat_l = []
        for x in l_jnts:
            flat_l += x

        c = Counter(flat_l)

        sorted_chains = []
        for l in l_jnts:
            nodes = []
            index = 1
            for i, j in enumerate(l[::-1]):
                if i == len(l) - 1:
                    nodes.append(j)
                    new = True
                    for a in sorted_chains:
                        if nodes == a:
                            new = False
                    if new:
                        sorted_chains.append(nodes)
                    break

                if c[j] == index:
                    nodes.append(j)
                else:
                    nodes.append(j)
                    new = True
                    for a in sorted_chains:
                        if nodes == a:
                            new = False
                    if new:
                        sorted_chains.append(nodes)

                    nodes = [j]
                    index = c[j]
        return sorted_chains

    def _get_joint_chain(self, end_effector: om.MDagPath, start_joint: om.MDagPath):

        joints = []

        while end_effector.fullPathName() != start_joint.fullPathName():
            end_effector.pop()
            effector = om.MFnTransform(end_effector)
            joints.insert(0, effector)

            if len(joints) <= 1:
                # Todo: add last joint which was used to place the end effector when the IKhandle was created.
                # is there a better way to do this?
                c = mc.listRelatives(end_effector.fullPathName(), children=1, type='joint')
                assert (len(c) == 1)
                dag = om.MSelectionList()
                dag.add(c[0])
                pth = om.MDagPath()
                dag.getDagPath(0, pth)
                joints.append(om.MFnTransform(pth))
                continue

        return joints

    def preSolve(self):
        """ function run before the actual solve is computed.

        ik chains could contain some mutual joints, if so then separate these
        into their own sub-chains.
        """
        # group all ikHandles together.
        self.setSingleChainOnly(False)
        self.ik_chains = []
        self.sub_nodes = {}
        self.ik_handles = {}
        raw_chains = []

        # get all chains
        # go through each chain and check
        handle_grp = self.handleGroup()
        for i in range(handle_grp.handleCount()):
            # get ik handle
            handle = handle_grp.handle(i)
            handle_path = om.MDagPath()
            om.MDagPath.getAPathTo(handle, handle_path)
            ik = oma.MFnIkHandle(handle_path)
            ik.setPriority(i)  # to avoid cycle errors, 1, 2 3 ... starting from end and working toward root

            # get end effector
            end_effector = om.MDagPath()
            ik.getEffector(end_effector)

            # get joint list
            split_names = end_effector.fullPathName().split('|')
            joint_list = ["|".join(split_names[:i]) for i, x in enumerate(split_names, 1)][1:-1]
            c = mc.listRelatives(joint_list[-1], children=1, type='joint')
            assert (len(c) == 1)
            joint_list.append(joint_list[-1] + '|' + c[0])

            raw_chains.append(joint_list)
            self.ik_handles[joint_list[-1]] = ik

        # sort array into unique list of joints.
        sorted_chains = self._sort_joint_chains(raw_chains)

        # add all joints to a list and count the occurrences of each element.
        sorted_flat = []
        for x in sorted_chains:
            sorted_flat += x
        sub_index = Counter(sorted_flat)

        # joints with multiple occurrences are sub-nodes
        sub_nodes = list(set([x for x, y in sub_index.items() if y >= 2]))

        # sort sub-nodes in hierarchy order
        sorted_sub_nodes = sorted(sub_nodes, key=lambda x: x.count('|'))

        # add joints to dictionary starting at the end of joint chains.
        for x in sorted_sub_nodes[::-1]:
            self.sub_nodes[x] = []

        # find and add sub-chains to a separate list
        sub_chains = []
        for x in sorted_chains:
            if x[0] in sorted_sub_nodes:
                sub_chains.append(x)
                continue

        for x in raw_chains:
            self.ik_chains.append(NodeChain(ik=self.ik_handles.get(x[-1], None), n=x))

        for x in sub_chains:
            node_l = x[::-1]
            j_c = NodeChain(n=node_l)
            j_c.isSub = True
            self.ik_chains.append(j_c)

        # get all nodes with no children
        # use counter to organise joints into list by count
        # 1 - leaf joint chains
        # 2+ - sub node joint chains

        # go down each chain and check for counts that are the same
        # when count is not equal, break. that's an IKChain, inclusive of last joint checked
        # if joints still left in original chain then repeat until finished
        # add these joints to a global flat list

        # next chain
        # if a joint is already part of a global flat list then break, its already been done.
        # but add a connection so the positions are passed to the child joint so it can average them out.

        """
             │      │    
            ┌┼┐    ┌┼┐   
         1  └┼┘    └┼┘  1
             │      │    
             │      │    
            ┌┼┐    ┌┼┐ 1 
         1  └┼┘    └┼┘   
             │  ┌─┐ │    
             └──┤ ├─┘    
                └┬┘  2   
          ┌─┐    │       
        1 └┼┘  ┌─┼┐      
           │   └─┼┘  2   
          ┌┼┐    │       
        1 └─┴───┬┼┐      
                └┼┘  3   
                 │       
                ┌┼┐      
                └─┘  3   
        """

    @staticmethod
    def _solve_nodes(nodes: list[om.MVector], links: list[float], target: om.MVector) -> list[om.MVector]:
        """ FABRIK algorithm to solve joint positions.

        The full paper is here:
        www.andreasaristidou.com/publications/papers/FABRIK.pdf

        Todo: Add rotation solving.
        Todo: Add rotation constraints to solve.

        Args:
            nodes: positions.
            links: distances between each node.
            target: position for end node, this can be the ik handle or another vector if a sub-node.

        Returns:
            updated positions.
        """
        node_pos = nodes
        dist = (node_pos[0] + (target * -1)).length()

        if dist > sum(links):
            # target is unreachable
            for i in range(0, len(node_pos) - 1, 1):
                # find distance(r) between target(t) and the joint(x).
                relative_dist = (target - node_pos[i]).length()
                relative_norm_dist = links[i] / relative_dist
                node_pos[i + 1] = node_pos[i] * (1 - relative_norm_dist) + target * relative_norm_dist

        else:
            # target is reachable so set b as the initial position
            b = node_pos[0]

            # distance between root and target.
            diff = (node_pos[-1] - target).length()
            count = 1

            while diff > 0.01:
                if count >= 10:
                    break
                # Stage 1: Forward Reaching(root<-effector)
                # set end effector as target
                node_pos[-1] = target
                for i in range(len(node_pos) - 2, -1, -1):
                    # find the distance(r) between the new joint point position
                    relative_dist = (node_pos[i + 1] - node_pos[i]).length()
                    try:
                        relative_norm_dist = links[i] / relative_dist
                    except ZeroDivisionError:
                        relative_norm_dist = links[i] / relative_dist

                    node_pos[i] = node_pos[i + 1] * (1 - relative_norm_dist) + node_pos[i] * relative_norm_dist

                # Stage 2: Backwards Reaching(root->effector)
                node_pos[0] = b
                for i in range(0, len(node_pos) - 1, 1):
                    # find the distance(r) between the new joint point position
                    relative_dist = (node_pos[i + 1] - node_pos[i]).length()
                    relative_norm_dist = links[i] / relative_dist
                    node_pos[i + 1] = node_pos[i] * (1 - relative_norm_dist) + node_pos[i + 1] * relative_norm_dist

                diff = (node_pos[-1] - target).length()
                count += 1

        return node_pos

    def doSolve(self) -> None:
        """ Overridden node function. """

        for my_chain in self.ik_chains:
            nodes = [n.name for n in my_chain.nodes]
            node_pos = [j.translation for j in my_chain.nodes]

            if my_chain.isSub:
                avg = om.MVector()
                pos = self.sub_nodes.get(nodes[-1])
                for p in pos:
                    avg += p
                target = avg / len(pos)
            else:
                target = my_chain.ik_handle

            new_pos = self._solve_nodes(node_pos, my_chain.links, target)

            stop = 0
            for x in nodes[::-1]:
                if x in self.sub_nodes.keys():
                    i = nodes.index(x)
                    self.sub_nodes[x].append(new_pos[i])
                    stop = 1
                    break

            for jv, pv in zip(my_chain.nodes[stop:], new_pos[stop:]):
                jv.translation = pv


def initializePlugin(plugin):
    _plugin = omx.MFnPlugin(plugin)
    try:
        _plugin.registerNode(kPluginNodeTypeName,
                              fabrikNodeId,
                              FabrikIKSolver.create,
                              FabrikIKSolver.initalize,
                              omx.MPxNode.kIkSolverNode,
                              'FABRIKIKSolver')
    except Exception as e:
        sys.stderr.write(f"Failed to register command: {kPluginNodeTypeName}\n")
        sys.stderr.write(f"{e}\n")
        raise


def uninitializePlugin(plugin):
    _plugin = omx.MFnPlugin(plugin)
    try:
        _plugin.deregisterNode(fabrikNodeId)
    except Exception as e:
        sys.stderr.write(f"Failed to unregister command: {kPluginNodeTypeName}\n")
        sys.stderr.write(f"{e}\n")
        raise
