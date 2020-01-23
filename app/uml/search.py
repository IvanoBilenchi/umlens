from __future__ import annotations

from collections import deque
from typing import Deque, Iterator, List, Optional, Set

from .classdiagram import Class, Diagram


class Node:
    """Allows searching for paths in the class diagram."""

    def __init__(self, diagram: Diagram, cls: Class, parent: Optional[Node] = None):
        self.diagram = diagram
        self.cls = cls
        self.parent = parent
        self.depth: int = parent.depth + 1 if parent else 0

    def __eq__(self, other: Node) -> bool:
        return self.cls == other.cls

    def __hash__(self) -> int:
        return self.cls.__hash__()

    def __repr__(self) -> str:
        return self.cls.__repr__()

    def children(self) -> Iterator[Node]:
        for cls in self.diagram.get_related_classes(self.cls):
            yield Node(self.diagram, cls, self)

    def path_to_root(self) -> List[Class]:
        path = []
        cur_node = self

        while cur_node:
            path.append(cur_node.cls)
            cur_node = cur_node.parent

        path.reverse()
        return path

    def search(self, goal: Class) -> List[Node]:
        solutions = []
        fringe: Deque[Node] = deque()
        closed: Set[Node] = set()
        fringe.append(self)

        while len(fringe):
            node = fringe.popleft()

            if node.cls == goal:
                solutions.append(node)

            if node not in closed:
                closed.add(node)
                fringe.extend(node.children())

        return solutions
