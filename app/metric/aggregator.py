from typing import Dict, List, Optional, Type

from app.cycle.finder import CycleFinder
from app.pattern.finder import PatternFinder
from app.uml.model import Diagram
from app.util.decorators import memoized
from .model import (
    AvgInheritanceDepth, AvgMethodsPerClass, AvgRelationshipsPerClass, Classes, ClassesInCycle,
    ClassesInCycleRatio, ClassesInPattern, ClassesInPatternRatio, ComputedMetric, DependencyCycles,
    DevelopmentCost, MethodInstances, Metric, Packages, PatternTypes, RelationshipInstances,
    RemediationCost, TechnicalDebtRatio
)


class MetricAggregator:

    def __init__(self, diagram: Diagram, cycle_finder: CycleFinder, pattern_finder: PatternFinder,
                 config: Optional[Dict] = None):
        self._diag = diagram
        self._cfinder = cycle_finder
        self._pfinder = pattern_finder
        self._config = config

    def compute_metrics(self) -> List[Metric]:
        metrics = self._base_metrics().copy()
        metrics.append(self._development_cost())
        metrics.append(self._remediation_cost())
        metrics.append(self._technical_debt_ratio())
        return metrics

    @memoized
    def _computed_metric(self, mtype: Type[ComputedMetric]) -> ComputedMetric:
        return mtype(self._diag, self._cfinder, self._pfinder)

    @memoized
    def _base_metrics(self) -> List[Metric]:
        metrics = [self._computed_metric(mtype)
                   for mtype in (Packages, Classes, PatternTypes, ClassesInPattern,
                                 MethodInstances, RelationshipInstances, AvgInheritanceDepth,
                                 DependencyCycles, ClassesInCycle)]

        for mtype, num, den in (
                (ClassesInPatternRatio, ClassesInPattern, Classes),
                (AvgMethodsPerClass, MethodInstances, Classes),
                (AvgRelationshipsPerClass, RelationshipInstances, Classes),
                (ClassesInCycleRatio, ClassesInCycle, Classes)
        ):
            metrics.append(mtype(self._computed_metric(num), self._computed_metric(den)))

        return metrics

    def _remediation_cost(self) -> RemediationCost:
        return RemediationCost([(m, self._config[m.identifier])
                                for m in self._base_metrics() if m.identifier in self._config])

    def _development_cost(self) -> DevelopmentCost:
        return DevelopmentCost(self._config.get(DevelopmentCost.id(), 0.0))

    def _technical_debt_ratio(self) -> TechnicalDebtRatio:
        return TechnicalDebtRatio(self._remediation_cost(), self._development_cost())
