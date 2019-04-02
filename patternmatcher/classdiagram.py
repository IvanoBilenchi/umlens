from enum import Enum, unique
from typing import List, Optional


class Element:
    """Models generic elements of the class diagram."""

    def __init__(self, identifier: str, name: str) -> None:
        if not (identifier and name):
            raise ValueError('Invalid falsy value.')

        self.identifier = identifier
        self.name = name

    def __str__(self) -> str:
        return self.name


class Datatype(Element):
    """Models datatypes."""

    def __str__(self) -> str:
        return '{}: datatype'.format(self.name)


class TypedElement(Element):
    """Models elements which have a datatype."""

    def __init__(self, identifier: str, name: str, datatype: Datatype) -> None:
        super().__init__(identifier=identifier, name=name)
        self.datatype = datatype

    def __str__(self) -> str:
        return '{}: {}'.format(self.name, self.datatype.name) if self.datatype else self.name


@unique
class Scope(Enum):
    """Models attribute and method scopes."""
    CLASS = 0
    INSTANCE = 1


class Parameter(TypedElement):
    """Models function parameters."""
    pass


class Attribute(TypedElement):
    """Models class attributes."""

    def __init__(self, identifier: str, name: str, datatype: Datatype,
                 scope: Scope = Scope.INSTANCE) -> None:
        super().__init__(identifier=identifier, name=name, datatype=datatype)
        self.scope = scope


class Method(Element):
    """Models methods."""

    def __init__(self, identifier: str, name: str, scope: Scope = Scope.INSTANCE,
                 abstract: bool = False) -> None:
        super().__init__(identifier=identifier, name=name)
        self.scope = scope
        self.abstract = abstract
        self.parameters: List[Parameter] = []
        self.return_type: Optional[Datatype] = None

    def __str__(self) -> str:
        args = ', '.join(str(a) for a in self.parameters)
        ret_type = self.return_type.name if self.return_type else 'void'
        return '{}({}): {}'.format(self.name, args, ret_type)

    def add_parameter(self, param: Parameter) -> None:
        self.parameters.append(param)


class Stereotype(Element):
    """Models stereotypes."""

    def __str__(self) -> str:
        return '<<{}>>'.format(self.name)


class Class(Datatype):
    """Models classes."""

    @property
    def is_interface(self) -> bool:
        return any(s.name == 'Interface' for s in self.stereotypes)

    def __init__(self, identifier: str, name: str, abstract: bool = False) -> None:
        super().__init__(identifier=identifier, name=name)
        self.abstract = abstract
        self.attributes: List[TypedElement] = []
        self.methods: List[Method] = []
        self.stereotypes: List[Stereotype] = []

    def __str__(self) -> str:
        header = '{}: class'.format(self.name)

        if self.stereotypes:
            header += ' <<{}>>'.format(', '.join(s.name for s in self.stereotypes))

        am_str = '\n'.join(['  {}'.format(a) for a in self.attributes] +
                           ['  {}'.format(m) for m in self.methods])

        return '{} {{\n{}\n}}'.format(header, am_str) if am_str else header


class Diagram:
    """Models a class diagram."""

    def __init__(self) -> None:
        self.datatypes = {}
        self.stereotypes = {}

    def get_class(self, identifier: str) -> Class:
        cls = self.datatypes.get(identifier, None)

        if not (cls and isinstance(cls, Class)):
            raise KeyError('No such class: ' + identifier)

        return cls

    def add_datatype(self, datatype: Datatype) -> None:
        self.datatypes[datatype.identifier] = datatype

    def add_stereotype(self, stereotype: Stereotype) -> None:
        self.stereotypes[stereotype.identifier] = stereotype

    def __str__(self) -> str:
        datatypes = list(self.datatypes.values())
        datatypes.sort(key=lambda d: d.name)
        return '\n'.join(str(d) for d in datatypes)
