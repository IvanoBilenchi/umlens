from .classdiagram import Diagram
from .decorators import memoized
from .finder import CycleFinder, PatternFinder


class Stats:
    """Computes statistics for a class diagram."""

    def __init__(self, diagram: Diagram, cycle_finder: CycleFinder, pattern_finder: PatternFinder):
        self._diag = diagram
        self._cycle_finder = cycle_finder
        self._pattern_finder = pattern_finder

    def __repr__(self) -> str:
        return ('Packages: {}\n'
                'Classes: {}\n'
                'Pattern types: {}\n'
                'Classes involved in patterns: {}\n'
                'Ratio of classes involved in patterns: {:.2f}\n'
                'Average methods per class: {:.2f}\n'
                'Average relationships per class: {:.2f}\n'
                'Average inheritance depth: {:.2f}\n'
                'Dependency cycles: {}\n'
                'Classes in cycles: {}\n'
                'Ratio of classes in cycles: {:.2f}'
                ).format(self.packages(), self.classes(), self.pattern_types(),
                         self.classes_in_pattern(), self.classes_in_pattern_ratio(),
                         self.avg_methods_per_class(), self.avg_relationships_per_class(),
                         self.avg_inheritance_depth(),
                         self.dependency_cycles(), self.classes_in_cycle(),
                         self.classes_in_cycle_ratio())

    @memoized
    def packages(self) -> int:
        return sum(1 for _ in self._diag.get_packages())

    @memoized
    def classes(self) -> int:
        return sum(1 for _ in self._diag.get_classes())

    @memoized
    def pattern_types(self) -> int:
        return len({p.name for p in self._pattern_finder.patterns()})

    @memoized
    def classes_in_pattern(self) -> int:
        return len({c for p in self._pattern_finder.patterns() for c in p.involved_classes})

    def classes_in_pattern_ratio(self) -> float:
        return self.classes_in_pattern() / self.classes()

    def dependency_cycles(self) -> int:
        return self._cycle_finder.cycle_count()

    @memoized
    def classes_in_cycle(self) -> int:
        return len({c for cycle in self._cycle_finder.cycles() for c in cycle.involved_classes})

    def classes_in_cycle_ratio(self) -> float:
        return self.classes_in_cycle() / self.classes()

    @memoized
    def avg_methods_per_class(self) -> float:
        cnt = sum(1 for c in self._diag.get_classes() for _ in self._diag.get_methods(c))
        return cnt / self.classes()

    @memoized
    def avg_relationships_per_class(self) -> float:
        cnt = sum(1 for c in self._diag.get_classes() for _ in self._diag.get_relationships(c))
        return cnt / self.classes()

    @memoized
    def avg_inheritance_depth(self) -> float:
        leaf_classes = list(self._diag.get_leaf_classes(exclude_standalone=True))
        cnt = sum(self._diag.get_inheritance_depth(c) for c in leaf_classes)
        return cnt / len(leaf_classes)
