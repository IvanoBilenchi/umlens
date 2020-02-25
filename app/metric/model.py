from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from typing import Generic, Iterable, Tuple, TypeVar, Union

from app.cycle.finder import CycleFinder
from app.pattern.finder import PatternFinder
from app.uml.model import Diagram
from app.util.decorators import cached_property, memoized

MetricValue = Union[int, float]
metric_eps = sys.float_info.epsilon
metric_inf = float('inf')

Numerator = TypeVar('Numerator', bound='Metric')
Denominator = TypeVar('Denominator', bound='Metric')


class Metric(ABC):
    """Models metrics and their computation."""
    _CC_REGEX = re.compile(r'(?<!^)(?=[A-Z])')

    # Override

    @property
    @abstractmethod
    def value(self) -> MetricValue:
        pass

    # Public

    @classmethod
    @memoized
    def id(cls) -> str:
        return cls._CC_REGEX.sub('_', cls.__name__).lower()

    @cached_property
    def name(self) -> str:
        return self._CC_REGEX.sub(' ', self.__class__.__name__).lower().capitalize()

    @property
    def identifier(self) -> str:
        return self.id()

    def __repr__(self) -> str:
        val = format(self.value, '.2f') if isinstance(self.value, float) else self.value
        return '{}: {}'.format(self.name, val)


class ProvidedMetric(Metric):
    """Models user-provided metrics."""

    @property
    def value(self) -> MetricValue:
        return self._value

    def __init__(self, value: MetricValue):
        self._value = value


class ComputedMetric(Metric, ABC):
    """Models metrics that are computed."""

    # Override

    @abstractmethod
    def _compute(self) -> MetricValue:
        pass

    # Public

    @cached_property
    def value(self) -> MetricValue:
        return self._compute()

    def __init__(self, diagram: Diagram, cycle_finder: CycleFinder, pattern_finder: PatternFinder):
        self._diag = diagram
        self._cfinder = cycle_finder
        self._pfinder = pattern_finder


class RatioMetric(Generic[Numerator, Denominator], Metric):
    """Models metrics that can be obtained as the ratio of two metrics."""

    def __init__(self, numerator: Numerator, denominator: Denominator):
        self.numerator = numerator
        self.denominator = denominator

    @property
    def value(self) -> MetricValue:
        num = self.numerator.value

        if num <= metric_eps:
            return 0.0

        den = self.denominator.value

        if den <= metric_eps:
            return metric_inf

        return num / den


class LinearCombinationMetric(Metric):
    """Models metrics that can be obtained as linear combinations of other metrics."""

    def __init__(self, metrics: Iterable[Tuple[Metric, float]]):
        self.metrics = metrics

    @property
    def value(self) -> MetricValue:
        return float(sum(m[0].value * m[1] for m in self.metrics))


class Packages(ComputedMetric):
    """Number of package."""

    def _compute(self) -> MetricValue:
        return sum(1 for _ in self._diag.packages())


class Classes(ComputedMetric):
    """Number of classes."""

    def _compute(self) -> MetricValue:
        return sum(1 for _ in self._diag.classes())


class PatternTypes(ComputedMetric):
    """Number of different design patterns."""

    def _compute(self) -> MetricValue:
        return len({p.name for p in self._pfinder.patterns()})


class ClassesInPattern(ComputedMetric):
    """Number of classes involved in patterns."""

    def _compute(self) -> MetricValue:
        return len({c for p in self._pfinder.patterns() for c in p.involved_classes})


class ClassesInPatternRatio(RatioMetric[ClassesInPattern, Classes]):
    """Ratio of classes involved in patterns."""
    pass


class DependencyCycles(ComputedMetric):
    """Number of dependency cycles."""

    def _compute(self) -> MetricValue:
        return self._cfinder.cycle_count()


class ClassesInCycle(ComputedMetric):
    """Number of classes that are in a dependency cycle."""

    def _compute(self) -> MetricValue:
        return len({c for cycle in self._cfinder.cycles() for c in cycle.involved_classes})


class ClassesInCycleRatio(RatioMetric[ClassesInCycle, Classes]):
    """Ratio of classes that are in a dependency cycle."""
    pass


class MethodInstances(ComputedMetric):
    """Number of method instances."""

    def _compute(self) -> MetricValue:
        return sum(1 for c in self._diag.classes() for _ in self._diag.methods(c))


class AvgMethodsPerClass(RatioMetric[MethodInstances, Classes]):
    """Average methods per class."""
    pass


class RelationshipInstances(ComputedMetric):
    """Number of relationship instances."""

    def _compute(self) -> MetricValue:
        return sum(1 for c in self._diag.classes() for _ in self._diag.relationships(c))


class AvgRelationshipsPerClass(RatioMetric[RelationshipInstances, Classes]):
    """Average relationships per class."""
    pass


class AvgInheritanceDepth(ComputedMetric):
    """Average depth of inheritance trees."""

    def _compute(self) -> MetricValue:
        leaf_classes = list(self._diag.leaf_classes(exclude_standalone=True))
        n_classes = len(leaf_classes)

        if n_classes == 0:
            return 0.0

        return sum(self._diag.inheritance_depth(c) for c in leaf_classes) / n_classes


class RemediationCost(LinearCombinationMetric):
    """Remediation cost."""
    pass


class DevelopmentCost(ProvidedMetric):
    """Development cost."""
    pass


class TechnicalDebtRatio(RatioMetric[RemediationCost, DevelopmentCost]):
    """Technical debt ratio."""
    pass
