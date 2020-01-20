from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Set, Type

from .classdiagram import Class, Diagram, RelType
from .matcher import Matcher
from .pattern import Pattern


class PatternFinder:
    """Finds patterns in class diagrams."""

    # Public

    def __init__(self, diagram: Diagram, matcher: Matcher) -> None:
        self._diagram = diagram
        self._matcher = matcher
        self._patterns: Dict[Class, List[Pattern]] = {}

    def patterns(self, cls: Optional[Class] = None,
                 kind: Optional[Type[Pattern]] = None) -> Iterator[Pattern]:
        self._find_patterns()
        returned = set()

        for c in [cls] if cls else self._patterns.keys():
            for p in self._patterns[c]:
                if (not kind or isinstance(p, kind)) and p not in returned:
                    returned.add(p)
                    yield p

    # Private

    def _find_patterns(self) -> None:
        if self._patterns:
            return

        for c in self._diagram.get_classes():
            for p in self._matcher.match(self._diagram, c):
                self._find_pattern(p)

    def _find_pattern(self, p: Pattern) -> None:
        for c in p.involved_classes:
            patterns = self._patterns.get(c, [])

            if not patterns:
                self._patterns[c] = patterns

            patterns.append(p)


class CycleInfo:
    """Contains information about dependency cycles."""

    def __init__(self, hierarchy: Set[Class], count: int):
        self.hierarchy = hierarchy
        self.count = count

    def __lt__(self, other: CycleInfo) -> bool:
        return min(self.hierarchy) < min(other.hierarchy)

    def __repr__(self) -> str:
        return '{} -> {}'.format(', '.join(str(c) for c in sorted(self.hierarchy)), self.count)


class CycleFinder:
    """Finds dependency cycles in class diagrams."""

    # Public

    def __init__(self, diagram: Diagram):
        self._diag = diagram
        self._cycles: List[CycleInfo] = []

    def cycle_count(self) -> int:
        return sum(c.count for c in self.cycles())

    def cycles(self) -> Iterator[CycleInfo]:
        self._find_cycles()
        yield from self._cycles

    # Private

    def _find_cycles(self) -> None:
        if self._cycles:
            return

        for hierarchy in self._hierarchies():
            count = 0

            for neigh in self._neighbors_for_hierarchy(hierarchy):
                count += self._cycles_for_hierarchy(hierarchy, neigh, set())

            if count:
                self._cycles.append(CycleInfo(hierarchy, count))

    def _hierarchies(self) -> Iterator[Set[Class]]:
        classes = set(self._diag.get_classes())

        while len(classes):
            cls = classes.pop()
            ancestors = set(self._diag.get_ancestors(cls))
            ancestors.add(cls)
            classes.difference_update(ancestors)
            yield ancestors

    def _neighbors_for_class(self, cls: Class) -> Iterator[Class]:
        return self._diag.get_related_classes(cls, kind=RelType.NON_HIERARCHICAL)

    def _neighbors_for_hierarchy(self, hierarchy: Set[Class]) -> Iterator[Class]:
        for cls in hierarchy:
            yield from self._neighbors_for_class(cls)

    def _cycles_for_hierarchy(self, hierarchy: Set[Class],
                              current: Class, visited: Set[Class]) -> int:
        count = 0

        for c in self._neighbors_for_class(current):
            if c in hierarchy:
                count += 1
            elif c not in visited:
                visited.add(c)
                count += self._cycles_for_hierarchy(hierarchy, c, visited)

        return count
