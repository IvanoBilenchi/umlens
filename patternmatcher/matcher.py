import re
from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable, List

from .classdiagram import AggType, Class, Diagram, Multiplicity, RelRole
from .pattern import (
    AbstractFactory, Adapter, Bridge, Composite, Decorator, Facade, FactoryMethod, Pattern,
    Prototype, Proxy
)


class Matcher(ABC):
    """Matcher abstract class."""

    @abstractmethod
    def match(self, dg: Diagram, cls: Class) -> Iterable[Pattern]:
        pass


class MultiMatcher(Matcher):
    """Matches patterns using multiple base matchers."""

    def __init__(self, *args):
        self._matchers: List[Matcher] = list(args)

    def match(self, dg: Diagram, cls: Class) -> Iterable[Pattern]:
        yield from (p for m in self._matchers for p in m.match(dg, cls))


class AbstractFactoryMatcher(Matcher):
    """Abstract factory matcher."""

    def __init__(self, factory_method_matcher: 'FactoryMethodMatcher') -> None:
        self._factory_method_matcher = factory_method_matcher

    def match(self, dg: Diagram, cls: Class) -> Iterable[AbstractFactory]:
        if not cls.is_interface:
            return

        # Find products
        pr = set(m.product for m in self._factory_method_matcher.match(dg, cls))

        if not pr:
            return

        # Find concrete factories
        cf = list(c for c in dg.get_realizations(cls)
                  if any(r for r in dg.get_dependencies(c, match=lambda r: r.is_creational)))

        if not cf:
            return

        # Find concrete products
        cp = set(p for f in cf for p in dg.get_dependencies(f, match=lambda r: r.is_creational))

        yield AbstractFactory(cls, list(pr), cf, list(cp))


class AdapterMatcher(Matcher):
    """Adapter matcher."""

    def match(self, dg: Diagram, cls: Class) -> Iterable[Adapter]:
        if not cls.is_interface:
            return

        # Find adapters
        adapters = dg.get_realizations(cls)

        for adapter in adapters:
            # Find adaptees
            adaptees = list(chain(
                dg.get_dependencies(adapter, match=lambda r: not r.is_creational),
                dg.get_super_classes(adapter)
            ))

            if len(adaptees) == 1 and _all_unique(cls, adapter, adaptees[0]):
                yield Adapter(cls, adapter, adaptees[0])


class BridgeMatcher(Matcher):
    """Bridge matcher."""

    def match(self, dg: Diagram, cls: Class) -> Iterable[Bridge]:
        if cls.is_interface:
            return

        # Find refined abstractions
        r_abs = list(dg.get_sub_classes(cls))

        if not r_abs:
            return

        # Find implementor
        impl = list(dg.get_associated_classes(cls, match=(lambda a:
                                                          a.aggregation_type in AggType.ANY)))

        if len(impl) != 1:
            return

        impl = impl[0]

        # Find concrete implementors
        concr = list(chain(dg.get_sub_classes(impl), dg.get_realizations(impl)))

        if _all_unique(cls, impl, *r_abs, *concr):
            yield Bridge(cls, impl, r_abs, concr)


class CompositeMatcher(Matcher):
    """Composite matcher."""

    def match(self, dg: Diagram, cls: Class) -> Iterable[Composite]:
        # Find leaves
        leaves = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(leaves) <= 1:
            return

        # Find composites
        composites = dg.get_associated_classes(cls,
                                               role=RelRole.RHS,
                                               match=(lambda a:
                                                      a.aggregation_type in AggType.ANY and
                                                      a.from_mult == Multiplicity.ONE and
                                                      a.to_mult in Multiplicity.MULTIPLE))
        composites = [c for c in composites if c in leaves]

        # Filter leaves
        leaves = [l for l in leaves if l not in composites]
        yield from (Composite(c, cls, leaves) for c in composites if _all_unique(c, cls, *leaves))


class DecoratorMatcher(Matcher):
    """Decorator matcher."""

    def match(self, dg: Diagram, cls: Class) -> Iterable[Decorator]:
        # Find concrete components
        cc = list(dg.get_realizations(cls) if cls.is_interface else dg.get_sub_classes(cls))

        if len(cc) <= 1:
            return

        # Find decorators
        decorators = dg.get_associated_classes(cls,
                                               role=RelRole.RHS,
                                               match=(lambda a:
                                                      a.aggregation_type in AggType.ANY and
                                                      a.from_mult in Multiplicity.ONE and
                                                      a.to_mult == Multiplicity.ONE))
        decorators = [d for d in decorators if (d in cc and dg.has_sub_classes(d))]

        # Filter concrete components
        cc = [c for c in cc if c not in decorators]

        for d in decorators:
            cd = list(dg.get_sub_classes(d))

            if _all_unique(d, cls, *cc, *cd):
                yield Decorator(d, cls, cc, cd)


class FacadeMatcher(Matcher):
    """Facade matcher."""

    def match(self, dg: Diagram, cls: Class) -> Iterable[Facade]:
        # Find dependencies
        deps = list(dg.get_dependencies(cls))
        if len(deps) > 2:
            yield Facade(cls, deps)


class FactoryMethodMatcher(Matcher):
    """Factory method matcher."""

    _regex = re.compile(r'^(?:alloc|build|construct|create|instantiate|new)', re.I)

    def match(self, dg: Diagram, cls: Class) -> Iterable[FactoryMethod]:
        # Find factory methods
        methods = (m for m in dg.get_methods(cls)
                   if isinstance(m.return_type, Class) and self._regex.match(m.name))

        created = list(dg.get_dependencies(cls, match=(lambda r:
                                                       (r.is_creational and
                                                        not r.to_cls.is_interface))))

        for m in methods:
            # Attempt to find specific types
            ret_type = m.return_type

            if ret_type.is_interface:
                ret_type = next((c for c in created if dg.is_realization(c, ret_type)), ret_type)

            yield FactoryMethod(cls, m, ret_type)


class PrototypeMatcher(Matcher):
    """Prototype matcher."""

    _copy_method_names = {'clone', 'copy'}

    def match(self, dg: Diagram, cls: Class) -> Iterable[Prototype]:
        if not (cls.is_interface and any(m for m in cls.methods
                                         if (m.return_type == cls and
                                             m.name in self._copy_method_names))):
            return

        # Find concrete prototypes
        cp = list(dg.get_realizations(cls))

        if not cp:
            return

        yield Prototype(cls, cp)


class ProxyMatcher(Matcher):
    """Proxy matcher."""

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
