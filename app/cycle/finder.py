from __future__ import annotations

from typing import Iterator, List, Set

from app.uml.model import Class, Diagram
from .search import Node


class Cycle:
    """Models dependency cycles."""

    def __init__(self, involved_classes: List[Class]):
        self.involved_classes = involved_classes

    def __eq__(self, other: Cycle) -> bool:
        # Cycle equality must be checked cyclically.
        if len(self.involved_classes) != len(other.involved_classes):
            return False

        cls_len = len(self.involved_classes)

        if cls_len == 0:
            return True

        new_list = self.involved_classes * 2

        for x in range(cls_len):
            z = 0
            for y in range(x, x + cls_len):
                if other.involved_classes[z] == new_list[y]:
                    z += 1
                else:
                    break

            if z == cls_len:
                return True

        return False

    def __hash__(self):
        # Hash must be invariant wrt cyclic equality.
        hval = 0
        for cls in self.involved_classes:
            hval ^= cls.__hash__()
        return hval

    def __lt__(self, other: Cycle) -> bool:
        return self.__repr__() < other.__repr__()

    def __repr__(self) -> str:
        return ', '.join(c.name for c in self.involved_classes)


class CycleFinder:
    """Finds dependency cycles in class diagrams."""

    # Public

    def __init__(self, diagram: Diagram):
        self._diag = diagram
        self._cycles: Set[Cycle] = set()

    def cycle_count(self) -> int:
        self._find_cycles()
        return len(self._cycles)

    def cycles(self) -> Iterator[Cycle]:
        self._find_cycles()
        yield from self._cycles

    # Private

    def _find_cycles(self) -> None:
        if self._cycles:
            return

        for cls in self._diag.classes():
            node = Node(self._diag, cls)

            for solution in node.search(cls):
                path = solution.path_to_root()
                path.pop()

                if len(path):
                    self._cycles.add(Cycle(path))
