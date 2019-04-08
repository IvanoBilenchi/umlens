from typing import Any, Type

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

    def create_finder(self, file_path: str) -> PatternFinder:
        return PatternFinder(self.create_diagram(file_path), self.create_multi_matcher())

    @memoized
    def create_multi_matcher(self) -> mt.MultiMatcher:
        return mt.MultiMatcher(
            self.create_matcher(mt.AbstractFactoryMatcher),
            self.create_matcher(mt.AdapterMatcher),
            self.create_matcher(mt.BridgeMatcher),
            self.create_matcher(mt.CompositeMatcher),
            self.create_matcher(mt.DecoratorMatcher),
            self.create_matcher(mt.FacadeMatcher),
            self.create_matcher(mt.FactoryMethodMatcher),
            self.create_matcher(mt.PrototypeMatcher),
            self.create_matcher(mt.ProxyMatcher)
        )

    @memoized
    def create_matcher(self, cls: Type[mt.Matcher]) -> Any:
        if cls == mt.AbstractFactoryMatcher:
            return mt.AbstractFactoryMatcher(self.create_matcher(mt.FactoryMethodMatcher))
        else:
            return cls()
