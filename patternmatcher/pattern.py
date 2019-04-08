from typing import List, Iterable
from . import classdiagram as cd


class Pattern:
    """Models design patterns."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def involved_classes(self) -> Iterable[cd.Class]:
        for v in self.__dict__.values():
            if isinstance(v, Iterable):
                yield from (c for c in v if isinstance(c, cd.Class))
            elif isinstance(v, cd.Class):
                yield v

    def __repr__(self) -> str:
        attrs = []

        for a, v in self.__dict__.items():
            if isinstance(v, Iterable):
                v = (str(i) for i in v)
                attrs.append('  {}: [{}]'.format(a, ', '.join(v)))
            else:
                attrs.append('  {}: {}'.format(a, str(v)))

        return '{} {{\n{}\n}}'.format(self.name, '\n'.join(attrs))


class AbstractFactory(Pattern):
    """Abstract factory pattern."""

    def __init__(self, abstract_factory: cd.Class, products: List[cd.Class],
                 concrete_factories: List[cd.Class], concrete_products: List[cd.Class]) -> None:
        self.abstract_factory = abstract_factory
        self.products = products
        self.concrete_factories = concrete_factories
        self.concrete_products = concrete_products


class Adapter(Pattern):
    """Adapter pattern."""

    def __init__(self, target: cd.Class, adapter: cd.Class, adaptee: cd.Class) -> None:
        self.target = target
        self.adapter = adapter
        self.adaptee = adaptee


class Bridge(Pattern):
    """Bridge pattern."""

    def __init__(self, abstraction: cd.Class, implementor: cd.Class,
                 refined_abstractions: List[cd.Class],
                 concrete_implementors: List[cd.Class]) -> None:
        self.abstraction = abstraction
        self.implementor = implementor
        self.refined_abstractions = refined_abstractions
        self.concrete_implementors = concrete_implementors


class Composite(Pattern):
    """Composite pattern."""

    def __init__(self, composite: cd.Class, component: cd.Class, leaves: List[cd.Class]) -> None:
        self.composite = composite
        self.component = component
        self.leaves = leaves


class Decorator(Pattern):
    """Decorator pattern."""

    def __init__(self, decorator: cd.Class, component: cd.Class,
                 concrete_components: List[cd.Class], concrete_decorators: List[cd.Class]) -> None:
        self.decorator = decorator
        self.component = component
        self.concrete_components = concrete_components
        self.concrete_decorators = concrete_decorators


class Facade(Pattern):
    """Facade pattern."""

    def __init__(self, facade: cd.Class, classes: List[cd.Class]) -> None:
        self.facade = facade
        self.classes = classes


class FactoryMethod(Pattern):
    """Factory pattern."""

    def __init__(self, factory: cd.Class, method: cd.Method, product: cd.Class) -> None:
        self.factory = factory
        self.method = method
        self.product = product


class Proxy(Pattern):
    """Proxy pattern."""

    def __init__(self, proxy: cd.Class, subject: cd.Class, real_subject: cd.Class) -> None:
        self.proxy = proxy
        self.subject = subject
        self.real_subject = real_subject
