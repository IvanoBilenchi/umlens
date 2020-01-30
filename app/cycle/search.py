from __future__ import annotations

from collections import deque
from typing import Deque, Iterator, List, Optional, Set

from app.uml.model import Class, Diagram


class Node:
    """Allows searching for paths in the class diagram."""

    def __init__(self, diagram: Diagram, cls: Class, parent: Optional[Node] = None):
        self._diag = diagram
        self._cls = cls
        self._parent = parent

    def __eq__(self, other: Node) -> bool:
        return self._cls == other._cls

    def __hash__(self) -> int:
        return self._cls.__hash__()

    def __repr__(self) -> str:
        return self._cls.__repr__()

    def children(self) -> Iterator[Node]:
        for cls in self._diag.related_classes(self._cls):
            yield Node(self._diag, cls, self)

    def path_to_root(self) -> List[Class]:
        path = []
        cur_node = self

        while cur_node:
            path.append(cur_node._cls)
            cur_node = cur_node._parent

        path.reverse()
        return path

    def search(self, goal: Class) -> List[Node]:
        solutions = []
        fringe: Deque[Node] = deque()
        closed: Set[Node] = set()
        fringe.append(self)

        while len(fringe):
            node = fringe.popleft()

            if node._cls == goal:
                solutions.append(node)

            if node not in closed:
                closed.add(node)
                fringe.extend(node.children())

        return solutions
