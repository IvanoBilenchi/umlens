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
