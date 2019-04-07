from enum import auto, Enum, Flag, unique
from typing import cast, Any, Dict, Iterable, List, Optional, Set


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

    def __init__(self, identifier: str, name: str, scope: Scope = Scope.INSTANCE,
                 abstract: bool = False) -> None:
        super().__init__(identifier=identifier, name=name)
        self.scope = scope
        self.abstract = abstract
        self.parameters: List[Parameter] = []
        self.return_type: Optional[Datatype] = None

    def __repr__(self) -> str:
        args = ', '.join(repr(a) for a in self.parameters)
        ret_type = self.return_type.name if self.return_type else 'void'
        return '{}({}): {}'.format(self.name, args, ret_type)

    def equals(self, other: 'Method') -> bool:
        return (self.name == other.name and
                self.scope == other.scope and
                self.return_type == other.return_type and
                all(m1.equals(m2) for (m1, m2) in zip(self.parameters, other.parameters)))

    def add_parameter(self, param: Parameter) -> None:
        self.parameters.append(param)


class Package(Element):
    """Models packages."""
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

    def has_attribute(self, attribute: Attribute) -> bool:
        return any(a.equals(attribute) for a in self.attributes)

    def has_method(self, method: Method) -> bool:
        return any(m.equals(method) for m in self.methods)

    def has_attributes(self, attributes: Iterable[Attribute]) -> bool:
        return all(self.has_attribute(a) for a in attributes)

    def has_methods(self, methods: Iterable[Method]) -> bool:
        return all(self.has_method(m) for m in methods)


class RelType(Flag):
    """Models class relationship types."""
    ASSOCIATION = auto()
    DEPENDENCY = auto()
    GENERALIZATION = auto()
    REALIZATION = auto()

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


@unique
class Multiplicity(Enum):
    """Models multiplicity classes."""
    ZERO = auto()
    ONE = auto()
    N = auto()
    STAR = auto()
    PLUS = auto()

    def is_multiple(self) -> bool:
        return not (self == self.ZERO or self == self.ONE)

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

    # Public

    def __init__(self) -> None:
        self._elements: Dict[str, Element] = {}
        self._relationships: Dict[str, Set[Relationship]] = {}

    def get_package(self, identifier: str) -> Package:
        return self._get_typed_element(Package, identifier)

    def get_class(self, identifier: str) -> Class:
        return self._get_typed_element(Class, identifier)

    def get_datatype(self, identifier: str) -> Datatype:
        return self._get_typed_element(Datatype, identifier)

    def get_stereotype(self, identifier: str) -> Stereotype:
        return self._get_typed_element(Stereotype, identifier)

    def get_relationship(self, identifier: str) -> Relationship:
        return self._get_typed_element(Relationship, identifier)

    def get_classes(self) -> Iterable[Class]:
        return (c for c in self._elements.values() if isinstance(c, Class))

    def get_relationships(self, cls: Class,
                          kind: Optional[RelType] = None,
                          role: RelRole = RelRole.ANY) -> Iterable[Relationship]:
        rel = self._relationships.get(cls.identifier, [])

        if kind:
            rel = (r for r in rel if r.rel_type in kind)

        if role == RelRole.LHS:
            rel = (r for r in rel if r.from_cls == cls)
        elif role == RelRole.RHS:
            rel = (r for r in rel if r.to_cls == cls)

        return rel

    def get_associations(self, cls: Class, agg_type: AggType = AggType.NONE,
                         role: RelRole = RelRole.RHS) -> Iterable[Association]:
        assoc = self.get_relationships(cls, kind=RelType.ASSOCIATION, role=role)
        assoc = cast(Iterable[Association], assoc)

        if agg_type == AggType.NONE:
            assoc = (a for a in assoc if a.aggregation_type == agg_type)
        else:
            assoc = (a for a in assoc if a.aggregation_type in agg_type)

        return assoc

    def get_related_classes(self, cls: Class,
                            kind: Optional[RelType] = None,
                            role: RelRole = RelRole.RHS) -> Iterable[Class]:
        ret = self.get_relationships(cls, kind=kind, role=role.opposite)
        return (r.to_cls if r.from_cls == cls else r.from_cls for r in ret)

    def get_associated_classes(self, cls: Class, agg_type: AggType = AggType.NONE,
                               role: RelRole = RelRole.RHS) -> Iterable[Class]:
        ret = self.get_associations(cls, agg_type=agg_type, role=role.opposite)
        return (r.to_cls if r.from_cls == cls else r.from_cls for r in ret)

    def get_sub_classes(self, cls: Class) -> Iterable[Class]:
        return self.get_related_classes(cls, kind=RelType.GENERALIZATION, role=RelRole.RHS)

    def get_super_classes(self, cls: Class) -> Iterable[Class]:
        return self.get_related_classes(cls, kind=RelType.GENERALIZATION, role=RelRole.LHS)

    def get_realizations(self, cls: Class) -> Iterable[Class]:
        if not cls.is_interface:
            return

        yield from self.get_related_classes(cls, kind=RelType.REALIZATION, role=RelRole.RHS)

    def get_interfaces(self, cls: Class) -> Iterable[Class]:
        return self.get_related_classes(cls, kind=RelType.REALIZATION, role=RelRole.LHS)

    def get_dependencies(self, cls: Class) -> Iterable[Class]:
        return self.get_related_classes(cls, kind=RelType.DEPENDENCY, role=RelRole.RHS)

    def get_dependants(self, cls: Class) -> Iterable[Class]:
        return self.get_related_classes(cls, kind=RelType.DEPENDENCY, role=RelRole.LHS)

    def add_element(self, element: Element) -> None:
        self._elements[element.identifier] = element

    def add_relationship(self, relationship: Relationship) -> None:
        self.add_element(relationship)

        for key in [relationship.from_cls.identifier, relationship.to_cls.identifier]:
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
