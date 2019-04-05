from enum import Enum, unique
from typing import Any, Dict, Iterable, List, Optional, Set


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


class Package(Element):
    """Models packages."""
    pass


class Class(Datatype):
    """Models classes."""

    @property
    def is_interface(self) -> bool:
        return any(s.name == 'Interface' for s in self.stereotypes)

    def __init__(self, identifier: str, name: str, abstract: bool = False,
                 package: Optional[Package] = None) -> None:
        super().__init__(identifier=identifier, name=name)
        self.abstract = abstract
        self.package = package
        self.attributes: List[TypedElement] = []
        self.methods: List[Method] = []

    def __str__(self) -> str:
        name = super().__str__()

        if self.package:
            name = '{}.{}'.format(self.package.name, name)

        am_str = '\n'.join(['  {}'.format(a) for a in self.attributes] +
                           ['  {}'.format(m) for m in self.methods])

        return '{} {{\n{}\n}}'.format(name, am_str) if am_str else name + ' {}'


class RelType(Enum):
    """Models class relationship types."""
    ASSOCIATION = 0
    DEPENDENCY = 1
    GENERALIZATION = 2
    REALIZATION = 3

    def to_string(self) -> str:
        return self.name.lower().capitalize()


class AggType(Enum):
    """Models class aggregation types."""
    NONE = 0
    SHARED = 1
    COMPOSITED = 2


class RelRole(Enum):
    """Models relationship roles."""
    LHS = 0
    RHS = 1
    ANY = 2


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

    def __init__(self, identifier: str, rel_type: RelType,
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

    def __str__(self) -> str:
        name = StereotypedElement.__str__(self)

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
            rel = (r for r in rel if r.rel_type == kind)

        if role == RelRole.LHS:
            rel = (r for r in rel if r.from_cls == cls)
        elif role == RelRole.RHS:
            rel = (r for r in rel if r.to_cls == cls)

        return rel

    def get_related_classes(self, cls: Class,
                            kind: Optional[RelType] = None,
                            role: RelRole = RelRole.ANY) -> Iterable[Class]:
        ret = self.get_relationships(cls, kind=kind)

        if role == RelRole.LHS:
            ret = (r.from_cls for r in ret if r.from_cls != cls or r.to_cls == cls)
        elif role == RelRole.RHS:
            ret = (r.to_cls for r in ret if r.to_cls != cls or r.from_cls == cls)
        else:
            ret = (r.to_cls if r.from_cls == cls else r.from_cls for r in ret)

        return ret

    def add_element(self, element: Element) -> None:
        self._elements[element.identifier] = element

    def add_relationship(self, relationship: Relationship) -> None:
        self.add_element(relationship)

        for key in [relationship.from_cls.identifier, relationship.to_cls.identifier]:
            relationships = self._relationships.get(key, set())

            if not relationships:
                self._relationships[key] = relationships

            relationships.add(relationship)

    def __str__(self) -> str:
        pk, dt, cl, st, rel = [], [], [], [], []

        for e in self._elements.values():
            if isinstance(e, Class):
                cl.append(str(e))
            elif isinstance(e, Stereotype):
                st.append(str(e))
            elif isinstance(e, Package):
                pk.append(str(e))
            elif isinstance(e, Relationship):
                rel.append(str(e))
            else:
                dt.append(str(e))

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
