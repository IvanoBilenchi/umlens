from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Type

from app.uml.model import Class, Diagram
from .matcher import Matcher
from .model import Pattern


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
