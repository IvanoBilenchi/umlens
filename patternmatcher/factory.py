from typing import Any, Iterable, List, Optional, Type

from . import classdiagram as cd
from . import json
from . import matcher as mt
from .decorators import memoized
from .finder import CycleFinder, PatternFinder
from .matcher import Matcher
from .metric import (
    AvgInheritanceDepth, AvgMethodsPerClass, AvgRelationshipsPerClass, Classes, ClassesInCycle,
    ClassesInCycleRatio, ClassesInPattern, ClassesInPatternRatio, ComputedMetric, DependencyCycles,
    DevelopmentCost, MethodInstances, Metric, Packages, PatternTypes, RelationshipInstances,
    RemediationCost, TechnicalDebtRatio
)
from .parser import Parser

MatcherType = Type[mt.Matcher]


class AppFactory:

    def __init__(self, diagram_path: str, config_path: Optional[str] = None):
        self.diagram_path = diagram_path
        self.config = json.load(config_path) if config_path else {}

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

    @memoized
    def create_metric(self, mtype: Type[ComputedMetric]) -> ComputedMetric:
        return mtype(self.create_diagram(),
                     self.create_cycle_finder(),
                     self.create_pattern_finder())

    @memoized
    def create_base_metrics(self) -> List[Metric]:
        metrics = [self.create_metric(mtype)
                   for mtype in (Packages, Classes, PatternTypes, ClassesInPattern,
                                 MethodInstances, RelationshipInstances, AvgInheritanceDepth,
                                 DependencyCycles, ClassesInCycle)]

        for mtype, num, den in (
            (ClassesInPatternRatio, ClassesInPattern, Classes),
            (AvgMethodsPerClass, MethodInstances, Classes),
            (AvgRelationshipsPerClass, RelationshipInstances, Classes),
            (ClassesInCycleRatio, ClassesInCycle, Classes)
        ):
            metrics.append(mtype(self.create_metric(num), self.create_metric(den)))

        return metrics

    def create_metrics(self) -> List[Metric]:
        metrics = self.create_base_metrics().copy()
        metrics.append(self.create_development_cost())
        metrics.append(self.create_remediation_cost())
        metrics.append(self.create_technical_debt_ratio())
        return metrics

    def create_remediation_cost(self) -> RemediationCost:
        return RemediationCost([(m, self.config[m.identifier])
                                for m in self.create_base_metrics() if m.identifier in self.config])

    def create_technical_debt_ratio(self) -> TechnicalDebtRatio:
        return TechnicalDebtRatio(self.create_remediation_cost(), self.create_development_cost())

    def create_development_cost(self) -> DevelopmentCost:
        return DevelopmentCost(self.config.get(DevelopmentCost.id(), 0.0))

    def create_multi_matcher(self, matchers: Iterable[Type[mt.Matcher]]) -> mt.MultiMatcher:
        return mt.MultiMatcher(*[self.create_matcher(m) for m in matchers])

    @memoized
    def create_matcher(self, cls: Type[mt.Matcher]) -> Any:
        if cls == mt.AbstractFactoryMatcher:
            return mt.AbstractFactoryMatcher(self.create_matcher(mt.FactoryMethodMatcher))
        else:
            return cls()
