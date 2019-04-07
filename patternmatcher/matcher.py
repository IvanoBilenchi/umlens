from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable, List, Type

from .classdiagram import AggType, Class, Diagram, Multiplicity, RelRole
from .pattern import Adapter, Bridge, Composite, Decorator, Pattern, Proxy


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

        for adapter in adapters:
            # Find adaptees
            adaptees = list(chain(dg.get_dependencies(adapter), dg.get_super_classes(adapter)))

            if len(adaptees) == 1 and _all_unique(cls, adapter, adaptees[0]):
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

        if _all_unique(cls, impl, *r_abs, *concr):
            yield Bridge(cls, impl, r_abs, concr)


class CompositeMatcher(Matcher):
    """Composite matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Composite

    def match(self, dg: Diagram, cls: Class) -> Iterable[Composite]:
        # Find leaves
        leaves = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(leaves) <= 1:
            return

        # Find composites
        composites = dg.get_associated_classes(cls, agg_type=AggType.ANY, role=RelRole.LHS,
                                               cls_mult=Multiplicity.MULTIPLE,
                                               other_mult=Multiplicity.ONE)
        composites = [c for c in composites if c in leaves]

        # Filter leaves
        leaves = [l for l in leaves if l not in composites]
        yield from (Composite(c, cls, leaves) for c in composites if _all_unique(c, cls, *leaves))


class DecoratorMatcher(Matcher):
    """Decorator matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Decorator

    def match(self, dg: Diagram, cls: Class) -> Iterable[Decorator]:
        # Find concrete components
        cc = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(cc) <= 1:
            return

        # Find decorators
        decorators = dg.get_associated_classes(cls, agg_type=AggType.ANY, role=RelRole.LHS,
                                               cls_mult=Multiplicity.ONE,
                                               other_mult=Multiplicity.ONE)
        decorators = [d for d in decorators if (d in cc and dg.has_sub_classes(d))]

        # Filter concrete components
        cc = [c for c in cc if c not in decorators]

        for d in decorators:
            cd = list(dg.get_sub_classes(d))

            if _all_unique(d, cls, *cc, *cd):
                yield Decorator(d, cls, cc, cd)


class ProxyMatcher(Matcher):
    """Proxy matcher."""

    @property
    def pattern_type(self) -> Type[Pattern]:
        return Proxy

    def match(self, dg: Diagram, cls: Class) -> Iterable[Proxy]:
        # Find proxies
        proxies = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(proxies) <= 1:
            return

        for p in proxies:
            if any(r for r in dg.get_associated_classes(p)):
                continue

            deps = list(r for r in dg.get_dependencies(p))

            if len(deps) == 1:
                real_subject = deps[0]

                if real_subject in proxies and _all_unique(p, cls, real_subject):
                    yield Proxy(p, cls, real_subject)


def _all_unique(*args) -> bool:
    seen = set()
    return not any(i in seen or seen.add(i) for i in args)
