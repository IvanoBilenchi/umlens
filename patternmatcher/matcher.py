from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable, List, Type

from .classdiagram import AggType, Class, Diagram, Multiplicity, RelRole
from .pattern import Adapter, Bridge, Composite, Pattern


class Matcher(ABC):
    """Matcher abstract class."""

    @property
    @abstractmethod
    def pattern_type(self) -> Type[Pattern]:
        return Pattern

    @abstractmethod
    def match(self, dg: Diagram, cls: Class) -> Iterable[Pattern]:
        pass

    @property
    def pattern_name(self) -> str:
        return self.pattern_type.__name__


class MultiMatcher(Matcher):
    """Matches patterns using multiple base matchers."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Pattern

    def __init__(self, *args):
        self._matchers: List[Matcher] = list(args)
        self._matchers.sort(key=lambda m: m.pattern_name)

    def match(self, dg: Diagram, cls: Class) -> Iterable[Pattern]:
        yield from (p for m in self._matchers for p in m.match(dg, cls))


class AdapterMatcher(Matcher):
    """Adapter matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Adapter

    def match(self, dg: Diagram, cls: Class) -> Iterable[Adapter]:
        if not cls.is_interface:
            return

        # Find adapters
        adapters = dg.get_realizations(cls)
        adapters = (c for c in adapters if c.has_methods(cls.methods))

        for adapter in adapters:
            # Find adaptees
            adaptees = list(chain(dg.get_dependencies(adapter), dg.get_super_classes(adapter)))

            if len(adaptees) == 1:
                yield Adapter(cls, adapter, adaptees[0])


class BridgeMatcher(Matcher):
    """Bridge matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Bridge

    def match(self, dg: Diagram, cls: Class) -> Iterable[Bridge]:
        if cls.is_interface:
            return

        # Find refined abstractions
        r_abs = list(dg.get_sub_classes(cls))

        if not r_abs:
            return

        # Find implementor
        impl = list(dg.get_associated_classes(cls, agg_type=AggType.ANY))

        if len(impl) != 1:
            return

        impl = impl[0]

        # Find concrete implementors
        concr = list(chain(dg.get_sub_classes(impl), dg.get_realizations(impl)))
        yield Bridge(cls, impl, r_abs, concr)


class CompositeMatcher(Matcher):
    """Composite matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Composite

    def match(self, dg: Diagram, cls: Class) -> Iterable[Pattern]:
        # Find leaves
        leaves = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(leaves) <= 1:
            return

        # Find composites
        composites = dg.get_associated_classes(cls, agg_type=AggType.ANY, role=RelRole.LHS,
                                               cls_mult=Multiplicity.MULTIPLE,
                                               other_mult=Multiplicity.ONE)
        composites = [c for c in composites if c in leaves and c.has_methods(cls.methods)]

        # Filter leaves
        leaves = [l for l in leaves if l not in composites]

        for c in composites:
            yield Composite(c, cls, leaves)
