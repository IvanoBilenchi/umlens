from typing import Any, Iterable, Optional, Type

from . import classdiagram as cd
from . import matcher as mt
from .decorators import memoized
from .finder import CycleFinder, PatternFinder
from .matcher import Matcher
from .parser import Parser
from .stats import Stats


MatcherType = Type[mt.Matcher]


class AppFactory:

    @staticmethod
    def create_parser() -> Parser:
        return Parser()

    @memoized
    def create_diagram(self, file_path: str) -> cd.Diagram:
        return AppFactory.create_parser().parse_document(file_path)

    def create_cycle_finder(self, file_path: str) -> CycleFinder:
        return CycleFinder(self.create_diagram(file_path))

    def create_pattern_finder(self, file_path: str,
                              matchers: Optional[Iterable[MatcherType]] = None) -> PatternFinder:
        if not matchers:
            matchers = Matcher.all().values()
        return PatternFinder(self.create_diagram(file_path), self.create_multi_matcher(matchers))

    def create_stats(self, file_path: str) -> Stats:
        return Stats(self.create_diagram(file_path),
                     self.create_cycle_finder(file_path),
                     self.create_pattern_finder(file_path))

    def create_multi_matcher(self, matchers: Iterable[Type[mt.Matcher]]) -> mt.MultiMatcher:
        return mt.MultiMatcher(*[self.create_matcher(m) for m in matchers])

    @memoized
    def create_matcher(self, cls: Type[mt.Matcher]) -> Any:
        if cls == mt.AbstractFactoryMatcher:
            return mt.AbstractFactoryMatcher(self.create_matcher(mt.FactoryMethodMatcher))
        else:
            return cls()
