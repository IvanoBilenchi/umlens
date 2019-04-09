from typing import Any, List, Type

from . import classdiagram as cd
from . import matcher as mt
from .decorators import memoized
from .parser import Parser
from .finder import PatternFinder


class AppFactory:

    @staticmethod
    def create_parser() -> Parser:
        return Parser()

    @staticmethod
    def create_diagram(file_path: str) -> cd.Diagram:
        return AppFactory.create_parser().parse_document(file_path)

    def create_finder(self, file_path: str, matchers: List[Type[mt.Matcher]]) -> PatternFinder:
        return PatternFinder(self.create_diagram(file_path), self.create_multi_matcher(matchers))

    def create_multi_matcher(self, matchers: List[Type[mt.Matcher]]) -> mt.MultiMatcher:
        return mt.MultiMatcher(*[self.create_matcher(m) for m in matchers])

    @memoized
    def create_matcher(self, cls: Type[mt.Matcher]) -> Any:
        if cls == mt.AbstractFactoryMatcher:
            return mt.AbstractFactoryMatcher(self.create_matcher(mt.FactoryMethodMatcher))
        else:
            return cls()
