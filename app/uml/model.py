from enum import Enum, Flag, auto, unique
from itertools import chain
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, cast


class Element:
    """Models generic elements of the class diagram."""

    def __init__(self, identifier: str, name: str) -> None:
        if not (identifier and name):
            raise ValueError('Invalid falsy value.')

        self.identifier = identifier
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        try:
            return self.identifier == other.identifier
        except AttributeError:
            return NotImplemented

    def __lt__(self, other) -> bool:
        try:
            return self.name < other.name
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return self.identifier.__hash__()


class Stereotype(Element):
    """Models stereotypes."""

    _creational_names = {'create', 'instantiate'}

    def is_creational(self) -> bool:
        return self.name in self._creational_names

    def __repr__(self) -> str:
        return '<<{}>>'.format(self.name)


class StereotypedElement(Element):
    """Models elements with stereotypes."""

    def __init__(self, identifier: str, name: str) -> None:
        super().__init__(identifier=identifier, name=name)
        self.stereotypes: List[Stereotype] = []

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
        return '{}: {}'.format(self.name, self.datatype.name) if self.datatype else self.name


@unique
class Scope(Enum):
    """Models attribute and method scopes."""
    CLASS = auto()
    INSTANCE = auto()


class Parameter(TypedElement):
    """Models function parameters."""

    def equals(self, other: 'Parameter') -> bool:
        return self.name == other.name and self.datatype == other.datatype


class Attribute(TypedElement):
    """Models class attributes."""

    def __init__(self, identifier: str, name: str, datatype: Datatype,
                 scope: Scope = Scope.INSTANCE) -> None:
        super().__init__(identifier=identifier, name=name, datatype=datatype)
        self.scope = scope

    def equals(self, other: 'Attribute') -> bool:
        return (self.name == other.name and
                self.scope == other.scope and
                self.datatype == other.datatype)


class Method(Element):
    """Models methods."""

    def __init__(self, identifier: str, name: str,
                 scope: Scope = Scope.INSTANCE,
                 abstract: bool = False,
                 parameters: Optional[List[Parameter]] = None,
                 return_type: Optional[Datatype] = None) -> None:
        super().__init__(identifier=identifier, name=name)
        self.scope = scope
        self.abstract = abstract
        self.parameters: List[Parameter] = parameters if parameters else []
        self.return_type: Optional[Datatype] = return_type

    def __repr__(self) -> str:
        args = ', '.join(repr(a) for a in self.parameters)
        ret_type = self.return_type.name if self.return_type else 'void'
        return '{}({}): {}'.format(self.name, args, ret_type)

    def equals(self, other: 'Method') -> bool:
        return (self.name == other.name and
                self.scope == other.scope and
                self.return_type == other.return_type and
                all(m1.equals(m2) for (m1, m2) in zip(self.parameters, other.parameters)))


class Package(Element):
    """Models package."""
    pass


class Class(Datatype):
    """Models classes."""

    @property
    def is_interface(self) -> bool:
        return any(s.name == 'Interface' for s in self.stereotypes)

    @property
    def qualified_name(self) -> str:
        name = self.name

        if self.package:
            name = '{}.{}'.format(self.package.name, name)

        return name

    def __init__(self, identifier: str, name: str, abstract: bool = False,
                 package: Optional[Package] = None) -> None:
        super().__init__(identifier=identifier, name=name)
        self.abstract = abstract
        self.package = package
        self.attributes: List[Attribute] = []
        self.methods: List[Method] = []

    def __repr__(self) -> str:
        name = super().__repr__()

        if self.package:
            name = '{}.{}'.format(self.package.name, name)

        am_str = '\n'.join(['  {}'.format(a) for a in self.attributes] +
                           ['  {}'.format(m) for m in self.methods])

        return '{} {{\n{}\n}}'.format(name, am_str) if am_str else name + ' {}'

    def __str__(self) -> str:
        return self.qualified_name


class RelType(Flag):
    """Models class relationship types."""
    ASSOCIATION = auto()
    DEPENDENCY = auto()
    GENERALIZATION = auto()
    REALIZATION = auto()

    ANY = ASSOCIATION | DEPENDENCY | GENERALIZATION | REALIZATION
    HIERARCHICAL = GENERALIZATION | REALIZATION
    NON_HIERARCHICAL = ASSOCIATION | DEPENDENCY

    def to_string(self) -> str:
        return self.name.lower().capitalize()


class AggType(Flag):
    """Models class aggregation types."""
    NONE = 0
    SHARED = auto()
    COMPOSITED = auto()
    ANY = SHARED | COMPOSITED


class RelRole(Flag):
    """Models relationship roles."""
    LHS = auto()
    RHS = auto()
    ANY = LHS | RHS

    @property
    def opposite(self) -> 'RelRole':
        if self == self.LHS:
            return self.RHS
        elif self == self.RHS:
            return self.LHS
        return self.ANY


class Multiplicity(Flag):
    """Models multiplicity classes."""
    ZERO = auto()
    ONE = auto()
    N = auto()
    STAR = auto()
    PLUS = auto()

    AT_MOST_ONE = ZERO | ONE
    MULTIPLE = N | STAR | PLUS
    ANY = AT_MOST_ONE | MULTIPLE

    def to_string(self) -> str:
        if self == Multiplicity.ZERO:
            return '0'
        elif self == Multiplicity.ONE:
            return '1'
        elif self == Multiplicity.N:
            return 'N'
        elif self == Multiplicity.STAR:
            return '0..*'
        elif self == Multiplicity.PLUS:
            return '1..*'


class Relationship(StereotypedElement):
    """Models class relationships."""

    @property
    def is_creational(self) -> bool:
        return (self.rel_type == RelType.DEPENDENCY and
                any(s.is_creational for s in self.stereotypes))

    def __init__(self, identifier: str, rel_type: RelType,
                 from_cls: Class, to_cls: Class) -> None:
        super().__init__(identifier=identifier, name=rel_type.to_string())
        self.rel_type = rel_type
        self.from_cls = from_cls
        self.to_cls = to_cls

    def __repr__(self) -> str:
        name = StereotypedElement.__repr__(self)
        return '{}({}, {})'.format(name, self.from_cls.name, self.to_cls.name)


class Association(Relationship):
    """Models class associations."""

    def __init__(self, identifier: str, agg_type: AggType,
                 from_cls: Class, to_cls: Class, from_mult: Multiplicity = Multiplicity.ONE,
                 to_mult: Multiplicity = Multiplicity.ONE) -> None:
        super().__init__(identifier=identifier, rel_type=RelType.ASSOCIATION,
                         from_cls=from_cls, to_cls=to_cls)
        self.aggregation_type = agg_type
        self.from_mult = from_mult
        self.to_mult = to_mult

        if agg_type == AggType.SHARED:
            self.name = 'Aggregation'
        elif agg_type == AggType.COMPOSITED:
            self.name = 'Composition'

    def __repr__(self) -> str:
        name = StereotypedElement.__repr__(self)

        def _mult_to_str(mult: Multiplicity) -> str:
            return '' if mult == Multiplicity.ONE else ' ({})'.format(mult.to_string())

        return '{}({}{}, {}{})'.format(name, self.from_cls.name, _mult_to_str(self.from_mult),
                                       self.to_cls.name, _mult_to_str(self.to_mult))


class Diagram:
    """Models a class diagram."""

    RelationshipMatch = Callable[[Relationship], bool]
    AssociationMatch = Callable[[Association], bool]

    # Public

    def __init__(self) -> None:
        self._elements: Dict[str, Element] = {}
        self._relationships: Dict[Element, Set[Relationship]] = {}

    def package(self, identifier: str) -> Package:
        return self._get_typed_element(Package, identifier)

    def cls(self, identifier: str) -> Class:
        return self._get_typed_element(Class, identifier)

    def datatype(self, identifier: str) -> Datatype:
        return self._get_typed_element(Datatype, identifier)

    def stereotype(self, identifier: str) -> Stereotype:
        return self._get_typed_element(Stereotype, identifier)

    def relationship(self, identifier: str) -> Relationship:
        return self._get_typed_element(Relationship, identifier)

    def classes(self, exclude_interfaces: bool = False) -> Iterator[Class]:
        return (c for c in self._elements.values()
                if isinstance(c, Class) and not (exclude_interfaces and c.is_interface))

    def packages(self) -> Iterator[Package]:
        return (p for p in self._elements.values() if isinstance(p, Package))

    def relationships(self, cls: Class,
                      kind: Optional[RelType] = None,
                      role: RelRole = RelRole.ANY,
                      match: RelationshipMatch = None) -> Iterator[Relationship]:
        rel = self._relationships.get(cls, [])

        if kind:
            rel = (r for r in rel if r.rel_type in kind)

        if role == RelRole.LHS:
            rel = (r for r in rel if r.from_cls == cls)
        elif role == RelRole.RHS:
            rel = (r for r in rel if r.to_cls == cls)

        if match:
            rel = (r for r in rel if match(r))

        return rel

    def associations(self, cls: Class, role: RelRole = RelRole.RHS,
                     match: AssociationMatch = None) -> Iterator[Association]:
        assoc = self.relationships(cls, kind=RelType.ASSOCIATION, role=role)
        assoc = cast(Iterator[Association], assoc)

        if match:
            assoc = (a for a in assoc if match(a))

        return assoc

    def related_classes(self, cls: Class,
                        kind: Optional[RelType] = None,
                        role: RelRole = RelRole.LHS,
                        match: RelationshipMatch = None) -> Iterator[Class]:
        return (r.to_cls if r.from_cls == cls else r.from_cls
                for r in self.relationships(cls, kind=kind, role=role, match=match))

    def associated_classes(self, cls: Class, role: RelRole = RelRole.LHS,
                           match: AssociationMatch = None) -> Iterator[Class]:
        return (r.to_cls if r.from_cls == cls else r.from_cls
                for r in self.associations(cls, role=role, match=match))

    def sub_classes(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        return self.related_classes(cls, kind=RelType.GENERALIZATION,
                                    role=RelRole.LHS, match=match)

    def super_classes(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        return self.related_classes(cls, kind=RelType.GENERALIZATION,
                                    role=RelRole.RHS, match=match)

    def leaf_classes(self, exclude_standalone: bool = False) -> Iterator[Class]:
        for c in self.classes(exclude_interfaces=True):
            if not self.has_sub_classes(c):
                if not exclude_standalone or self.has_super_classes(c):
                    yield c

    def ancestors(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        for c in self.super_classes(cls, match):
            yield c
            yield from self.ancestors(c, match)

    def realizations(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        if not cls.is_interface:
            return

        yield from self.related_classes(cls, kind=RelType.REALIZATION,
                                        role=RelRole.LHS, match=match)

    def interfaces(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        return self.related_classes(cls, kind=RelType.REALIZATION,
                                    role=RelRole.RHS, match=match)

    def dependencies(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        return self.related_classes(cls, kind=RelType.DEPENDENCY,
                                    role=RelRole.LHS, match=match)

    def dependants(self, cls: Class, match: RelationshipMatch = None) -> Iterator[Class]:
        return self.related_classes(cls, kind=RelType.DEPENDENCY,
                                    role=RelRole.RHS, match=match)

    def is_sub_class(self, sub_cls: Class, super_cls: Class) -> bool:
        return any(c for c in self.sub_classes(super_cls) if c == sub_cls)

    def is_realization(self, realization: Class, interface: Class) -> bool:
        return (interface.is_interface and
                any(c for c in self.realizations(interface) if c == realization))

    def has_sub_classes(self, cls: Class) -> bool:
        return any(self.sub_classes(cls))

    def has_super_classes(self, cls: Class) -> bool:
        return any(self.super_classes(cls))

    def has_realizations(self, cls: Class) -> bool:
        return any(self.realizations(cls))

    def inheritance_depth(self, cls: Class, start_depth: int = 0) -> int:
        depth = start_depth

        for c in self.super_classes(cls):
            depth = max(self.inheritance_depth(c, start_depth=start_depth + 1), depth)

        return depth

    def methods(self, cls: Class) -> Iterator[Method]:
        yield from cls.methods

        for c in chain(self.interfaces(cls), self.super_classes(cls)):
            yield from self.methods(c)

    def add_element(self, element: Element) -> None:
        self._elements[element.identifier] = element

    def add_relationship(self, relationship: Relationship) -> None:
        self.add_element(relationship)

        for key in (relationship.from_cls, relationship.to_cls):
            relationships = self._relationships.get(key, set())

            if not relationships:
                self._relationships[key] = relationships

            relationships.add(relationship)

    def __repr__(self) -> str:
        pk, dt, cl, st, rel = [], [], [], [], []

        for e in self._elements.values():
            if isinstance(e, Class):
                cl.append(repr(e))
            elif isinstance(e, Stereotype):
                st.append(repr(e))
            elif isinstance(e, Package):
                pk.append(repr(e))
            elif isinstance(e, Relationship):
                rel.append(repr(e))
            else:
                dt.append(repr(e))

        pk.sort()
        dt.sort()
        cl.sort()
        st.sort()
        rel.sort()

        pk = 'Packages:\n---------\n' + '\n'.join(pk)
        dt = 'Datatypes:\n----------\n' + '\n'.join(dt)
        cl = 'Classes:\n--------\n' + '\n'.join(cl)
        st = 'Stereotypes:\n------------\n' + '\n'.join(st)
        rel = 'Relationships:\n--------------\n' + '\n'.join(rel)

        return '\n\n'.join([pk, dt, st, cl, rel])

    # Private

    def _get_typed_element(self, kind: type, identifier: str) -> Any:
        el = self._elements.get(identifier, None)

        if not (el and isinstance(el, kind)):
            raise KeyError('No such {}: {}'.format(str(kind), identifier))

        return el
