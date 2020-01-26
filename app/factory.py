from typing import Any, Iterable, Optional, Type

from .cycle.finder import CycleFinder
from .metric.aggregator import MetricAggregator
from .pattern import matcher as mt
from .pattern.finder import PatternFinder
from .pattern.matcher import Matcher
from .uml import model as cd
from .uml.parser import Parser
from .util import json
from .util.decorators import memoized

MatcherType = Type[mt.Matcher]


class AppFactory:

    def __init__(self, diagram_path: str):
        self.diagram_path = diagram_path

    @classmethod
    def create_parser(cls) -> Parser:
        return Parser()

    @memoized
    def create_diagram(self) -> cd.Diagram:
        return self.create_parser().parse_document(self.diagram_path)

    def create_cycle_finder(self) -> CycleFinder:
        return CycleFinder(self.create_diagram())

    def create_pattern_finder(self,
                              matchers: Optional[Iterable[MatcherType]] = None) -> PatternFinder:
        if not matchers:
            matchers = Matcher.all().values()
        return PatternFinder(self.create_diagram(), self.create_multi_matcher(matchers))

    def create_multi_matcher(self, matchers: Iterable[Type[mt.Matcher]]) -> mt.MultiMatcher:
        return mt.MultiMatcher(*[self.create_matcher(m) for m in matchers])

    def create_metrics(self, config_path: Optional[str] = None) -> MetricAggregator:
        config = json.load(config_path) if config_path else {}
        return MetricAggregator(self.create_diagram(), self.create_cycle_finder(),
                                self.create_pattern_finder(), config)

    @memoized
    def create_matcher(self, cls: Type[mt.Matcher]) -> Any:
        if cls == mt.AbstractFactoryMatcher:
            return mt.AbstractFactoryMatcher(self.create_matcher(mt.FactoryMethodMatcher))
        else:
            return cls()
