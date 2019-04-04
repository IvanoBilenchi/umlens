from enum import Enum, unique
from typing import Dict, List, Optional


class Element:
    """Models generic elements of the class diagram."""

    def __init__(self, identifier: str, name: str) -> None:
        if not (identifier and name):
            raise ValueError('Invalid falsy value.')

        self.identifier = identifier
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, Element):
            return self.identifier == other.identifier
        return False

    def __hash__(self):
        return self.identifier.__hash__()


class Stereotype(Element):
    """Models stereotypes."""

    def __str__(self) -> str:
        return '<<{}>>'.format(self.name)


class StereotypedElement(Element):
    """Models elements with stereotypes."""

    def __init__(self, identifier: str, name: str) -> None:
        super().__init__(identifier=identifier, name=name)
        self.stereotypes: List[Stereotype] = []

    def __str__(self) -> str:
        if self.stereotypes:
            stereotypes = ' <<{}>>'.format(', '.join(s.name for s in self.stereotypes))
        else:
            stereotypes = ''

        return self.name + stereotypes


class Datatype(StereotypedElement):
    """Models datatypes."""
    pass


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

    def __str__(self) -> str:
        header = super().__str__()
        am_str = '\n'.join(['  {}'.format(a) for a in self.attributes] +
                           ['  {}'.format(m) for m in self.methods])

        return '{} {{\n{}\n}}'.format(header, am_str) if am_str else header + ' {}'


class RelationshipType(Enum):
    """Models class relationship types."""
    ASSOCIATION = 0
    DEPENDENCY = 1
    GENERALIZATION = 2
    REALIZATION = 3

    def to_string(self) -> str:
        return self.name.lower().capitalize()


class AggregationType(Enum):
    """Models class aggregation types."""
    NONE = 0
    SHARED = 1
    COMPOSITED = 2


class Multiplicity(Enum):
    """Models multiplicity classes."""
    ZERO = 0
    ONE = 1
    N = 2
    STAR = 3
    PLUS = 4

    def is_multiple(self) -> bool:
        return self.value > 1

    def to_string(self) -> str:
        if self == Multiplicity.N:
            return 'N'
        elif self == Multiplicity.STAR:
            return '0..*'
        elif self == Multiplicity.PLUS:
            return '1..*'
        else:
            return str(self.value)


class Relationship(StereotypedElement):
    """Models class relationships."""

    def __init__(self, identifier: str, rel_type: RelationshipType,
                 from_cls: Class, to_cls: Class) -> None:
        super().__init__(identifier=identifier, name=rel_type.to_string())
        self.rel_type = rel_type
        self.from_cls = from_cls
        self.to_cls = to_cls

    def __str__(self) -> str:
        name = StereotypedElement.__str__(self)
        return '{}({}, {})'.format(name, self.from_cls.name, self.to_cls.name)


class Association(Relationship):
    """Models class associations."""

    def __init__(self, identifier: str, agg_type: AggregationType,
                 from_cls: Class, to_cls: Class, from_mult: Multiplicity = Multiplicity.ONE,
                 to_mult: Multiplicity = Multiplicity.ONE) -> None:
        super().__init__(identifier=identifier, rel_type=RelationshipType.ASSOCIATION,
                         from_cls=from_cls, to_cls=to_cls)
        self.aggregation_type = agg_type
        self.from_mult = from_mult
        self.to_mult = to_mult

        if agg_type == AggregationType.SHARED:
            self.name = 'Aggregation'
        elif agg_type == AggregationType.COMPOSITED:
            self.name = 'Composition'

    def __str__(self) -> str:
        name = StereotypedElement.__str__(self)

        def _mult_to_str(mult: Multiplicity) -> str:
            return '' if mult == Multiplicity.ONE else ' ({})'.format(mult.to_string())

        return '{}({}{}, {}{})'.format(name, self.from_cls.name, _mult_to_str(self.from_mult),
                                       self.to_cls.name, _mult_to_str(self.to_mult))


class Diagram:
    """Models a class diagram."""

    def __init__(self) -> None:
        self.datatypes: Dict[str, Datatype] = {}
        self.stereotypes: Dict[str, Stereotype] = {}
        self.relationships: Dict[(str, str), List[Relationship]] = {}

    def get_class(self, identifier: str) -> Class:
        cls = self.datatypes.get(identifier, None)

        if not (cls and isinstance(cls, Class)):
            raise KeyError('No such class: ' + identifier)

        return cls

    def add_datatype(self, datatype: Datatype) -> None:
        self.datatypes[datatype.identifier] = datatype

    def add_stereotype(self, stereotype: Stereotype) -> None:
        self.stereotypes[stereotype.identifier] = stereotype

    def add_relationship(self, relationship: Relationship) -> None:
        key = (relationship.from_cls.identifier, relationship.to_cls.identifier)

        relationships = self.relationships.get(key, [])

        if not relationships:
            self.relationships[key] = relationships

        relationships.append(relationship)

    def __str__(self) -> str:
        dt = list(self.datatypes.values())
        dt.sort(key=lambda d: d.name)

        cl = [d for d in dt if isinstance(d, Class)]
        dt = [d for d in dt if not isinstance(d, Class)]

        dt = 'Datatypes:\n----------\n' + '\n'.join(str(d) for d in dt)
        cl = 'Classes:\n--------\n' + '\n'.join(str(c) for c in cl)

        st = list(self.stereotypes.values())
        st.sort(key=lambda s: s.name)
        st = 'Stereotypes:\n------------\n' + '\n'.join(str(s) for s in st)

        rel = [r for sublist in self.relationships.values() for r in sublist]
        rel.sort(key=lambda r: str(r))
        rel = 'Relationships:\n--------------\n' + '\n'.join(str(r) for r in rel)

        return '\n\n'.join([dt, st, cl, rel])
