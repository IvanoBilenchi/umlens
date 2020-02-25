import xml.etree.ElementTree as Et
from typing import Optional

from . import model as cd


class XT:
    """XML tags namespace."""
    ASSOCIATION = 'Association'
    ASSOCIATION_END = 'AssociationEnd'
    ATTRIBUTE = 'Attribute'
    CLASS = 'Class'
    DATATYPE = 'DataType'
    DEPENDENCY = 'Dependency'
    FROM_END = 'FromEnd'
    GENERALIZATION = 'Generalization'
    MODEL_CHILDREN = 'ModelChildren'
    MODEL_RELATIONSHIP_CONTAINER = 'ModelRelationshipContainer'
    MODELS = 'Models'
    OPERATION = 'Operation'
    PACKAGE = 'Package'
    PARAMETER = 'Parameter'
    REALIZATION = 'Realization'
    RET_TYPE = 'ReturnType'
    STEREOTYPE = 'Stereotype'
    STEREOTYPES = 'Stereotypes'
    TO_END = 'ToEnd'
    TYPE = 'Type'
    USAGE = 'Usage'

    @staticmethod
    def path(*args) -> str:
        return './' + '/'.join(args)


class XA:
    """XML attributes namespace."""
    ABSTRACT = 'Abstract'
    AGGREGATION_KIND = 'AggregationKind'
    END_MODEL_ELEMENT = 'EndModelElement'
    FROM = 'From'
    ID = 'Id'
    ID_REF = 'Idref'
    MULTIPLICITY = 'Multiplicity'
    NAME = 'Name'
    SCOPE = 'Scope'
    TO = 'To'


# noinspection PyBroadException
class Parser:

    # Public

    def __init__(self) -> None:
        self._diagram = cd.Diagram()

    def parse_document(self, file_path: str) -> cd.Diagram:
        models: Et.Element = Et.parse(file_path).getroot().find(XT.MODELS)

        self._parse_stereotypes(models)
        self._parse_datatypes(models)
        self._parse_classes(models)
        self._parse_packages(models)
        self._parse_relationships(models)

        return self._diagram

    # Private

    @staticmethod
    def _parse_identifier(node: Et.Element, attr: str = XA.ID) -> str:
        try:
            return node.attrib[attr]
        except Exception as e:
            raise Exception('Node has no identifier: {} {}'.format(node.tag, node.attrib)) from e

    @staticmethod
    def _parse_name(node: Et.Element) -> str:
        return node.attrib.get(XA.NAME, '')

    @staticmethod
    def _parse_abstract(node: Et.Element) -> bool:
        return node.attrib.get(XA.ABSTRACT, 'false') == 'true'

    @staticmethod
    def _parse_scope(node: Et.Element) -> cd.Scope:
        if node.attrib.get(XA.SCOPE, 'instance') == 'instance':
            return cd.Scope.INSTANCE
        return cd.Scope.CLASS

    @staticmethod
    def _parse_mult(node: Et.Element) -> cd.Multiplicity:
        mult_str: str = node.attrib[XA.MULTIPLICITY]
        if mult_str == '0':
            return cd.Multiplicity.ZERO
        elif mult_str in ['1', 'Unspecified']:
            return cd.Multiplicity.ONE
        elif mult_str in ['*', '0..*']:
            return cd.Multiplicity.STAR
        elif mult_str in ['+', '1..*']:
            return cd.Multiplicity.PLUS
        elif mult_str.isdigit():
            return cd.Multiplicity.N
        else:
            return cd.Multiplicity.ONE

    @staticmethod
    def _parse_rel_type(node: Et.Element) -> Optional[cd.RelType]:
        try:
            return cd.RelType[node.tag.upper()]
        except Exception:
            if node.tag == XT.USAGE:
                return cd.RelType.DEPENDENCY
            raise

    @staticmethod
    def _parse_agg_type(node: Et.Element) -> cd.AggType:
        try:
            return cd.AggType[node.attrib[XA.AGGREGATION_KIND].upper()]
        except Exception:
            return cd.AggType.NONE

    def _parse_packages(self, node: Et.Element) -> None:
        for package_node in node.findall(XT.PACKAGE):
            package = self._create_package(package_node)

            for child in package_node.findall(XT.MODEL_CHILDREN):
                self._parse_classes(child, package=package)

    def _parse_datatypes(self, node: Et.Element) -> None:
        for model in node.findall(XT.DATATYPE):
            self._create_datatype(model)

    def _parse_classes(self, node: Et.Element, package: Optional[cd.Package] = None) -> None:
        for model in node.findall(XT.CLASS):
            self._create_class(model, package=package)

        for model in node.findall(XT.CLASS):
            self._populate_class(model)

    def _parse_stereotypes(self, node: Et.Element) -> None:
        for model in node.findall(XT.STEREOTYPE):
            self._create_stereotype(model)

    def _parse_relationships(self, node: Et.Element) -> None:
        for tag in [XT.DEPENDENCY, XT.GENERALIZATION, XT.REALIZATION, XT.USAGE]:
            for child in node.iter(tag):
                self._create_relationship(child)

        for child in node.iter(XT.ASSOCIATION):
            self._create_association(child)

    def _create_package(self, node: Et.Element) -> cd.Package:
        package = cd.Package(
            identifier=Parser._parse_identifier(node),
            name=Parser._parse_name(node)
        )
        self._diagram.add_element(package)
        return package

    def _create_datatype(self, node: Et.Element) -> cd.Datatype:
        datatype = cd.Datatype(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node)
        )
        self._diagram.add_element(datatype)
        return datatype

    def _create_class(self, node: Et.Element, package: Optional[cd.Package] = None) -> cd.Class:
        cls = cd.Class(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node),
            abstract=self._parse_abstract(node),
            package=package
        )
        self._diagram.add_element(cls)
        return cls

    def _create_stereotype(self, node: Et.Element) -> cd.Stereotype:
        stereotype = cd.Stereotype(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node)
        )
        self._diagram.add_element(stereotype)
        return stereotype

    def _create_relationship(self, node: Et.Element) -> None:
        try:
            relationship = cd.Relationship(
                identifier=self._parse_identifier(node),
                rel_type=self._parse_rel_type(node),
                from_cls=self._diagram.cls(self._parse_identifier(node, attr=XA.FROM)),
                to_cls=self._diagram.cls(self._parse_identifier(node, attr=XA.TO))
            )

            self._add_stereotypes(relationship, node)
            self._diagram.add_relationship(relationship)
        except Exception:
            return

    def _create_association(self, node: Et.Element) -> None:
        try:
            from_node = node.find(XT.path(XT.FROM_END, XT.ASSOCIATION_END))
            to_node = node.find(XT.path(XT.TO_END, XT.ASSOCIATION_END))

            from_cls_id = self._parse_identifier(from_node, attr=XA.END_MODEL_ELEMENT)
            to_cls_id = self._parse_identifier(to_node, attr=XA.END_MODEL_ELEMENT)

            association = cd.Association(
                identifier=self._parse_identifier(node),
                agg_type=self._parse_agg_type(from_node),
                from_cls=self._diagram.cls(from_cls_id),
                to_cls=self._diagram.cls(to_cls_id),
                from_mult=self._parse_mult(from_node),
                to_mult=self._parse_mult(to_node)
            )

            self._add_stereotypes(association, node)
            self._diagram.add_relationship(association)
        except Exception:
            return

    def _populate_class(self, node: Et.Element) -> None:
        cls = self._diagram.cls(self._parse_identifier(node))
        ch_node = node.find(XT.MODEL_CHILDREN)

        if ch_node:
            for child in ch_node.findall(XT.ATTRIBUTE):
                self._add_attribute(cls, child)

            for child in ch_node.findall(XT.OPERATION):
                self._add_method(cls, child)

        self._add_stereotypes(cls, node)

    def _add_attribute(self, cls: cd.Class, node: Et.Element) -> None:
        attr = cd.Attribute(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node),
            datatype=self._get_ref_datatype(node.find(XT.TYPE)),
            scope=self._parse_scope(node)
        )
        cls.attributes.append(attr)

    def _add_method(self, cls: cd.Class, node: Et.Element) -> None:
        parameters = [
            cd.Parameter(identifier=self._parse_identifier(child),
                         name=self._parse_name(child),
                         datatype=self._get_ref_datatype(child.find(XT.TYPE)))
            for child in node.iter(XT.PARAMETER)
        ]

        method = cd.Method(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node),
            scope=self._parse_scope(node),
            abstract=self._parse_abstract(node),
            parameters=parameters,
            return_type=self._get_ref_datatype(node.find(XT.RET_TYPE))
        )

        cls.methods.append(method)

    def _add_stereotypes(self, element: cd.StereotypedElement, node: Et.Element) -> None:
        for child in node.findall(XT.path(XT.STEREOTYPES, XT.STEREOTYPE)):
            stereotype = self._get_ref_stereotype(child)
            if stereotype:
                element.stereotypes.append(stereotype)

    def _get_ref_datatype(self, node: Et.Element) -> Optional[cd.Datatype]:
        try:
            return self._diagram.datatype(self._parse_identifier(node[0], attr=XA.ID_REF))
        except Exception:
            return None

    def _get_ref_stereotype(self, node: Et.Element) -> Optional[cd.Stereotype]:
        try:
            return self._diagram.stereotype(self._parse_identifier(node, attr=XA.ID_REF))
        except Exception:
            return None
