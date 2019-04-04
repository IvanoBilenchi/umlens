import xml.etree.ElementTree as Et
from typing import Optional

from . import classdiagram as cd


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


class Parser:

    # Public

    def __init__(self) -> None:
        self._diagram = cd.Diagram()

    def parse_document(self, file_path: str) -> cd.Diagram:
        node: Et.Element = Et.parse(file_path).getroot().find(XT.MODELS)
        self._parse_datatypes(node)

        node = node.find(XT.path(XT.MODEL_RELATIONSHIP_CONTAINER, XT.MODEL_CHILDREN))
        self._parse_relationships(node)

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
        return cd.Scope.INSTANCE if node.attrib.get(XA.SCOPE, 'instance') else cd.Scope.CLASS

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
    def _parse_rel_type(node: Et.Element) -> Optional[cd.RelationshipType]:
        try:
            return cd.RelationshipType[node.tag.upper()]
        except Exception:
            if node.tag == XT.USAGE:
                return cd.RelationshipType.DEPENDENCY
            raise

    @staticmethod
    def _parse_agg_type(node: Et.Element) -> cd.AggregationType:
        try:
            return cd.AggregationType[node.attrib[XA.AGGREGATION_KIND].upper()]
        except Exception:
            return cd.AggregationType.NONE

    def _parse_datatypes(self, node: Et.Element) -> None:
        for model in node.findall(XT.STEREOTYPE):
            self._create_stereotype(model)

        for model in node.findall(XT.DATATYPE):
            self._create_datatype(model)

        for model in node.findall(XT.CLASS):
            self._create_class(model)

        for model in node.findall(XT.CLASS):
            self._populate_class(model)

    def _parse_relationships(self, node: Et.Element) -> None:
        for tag in [XT.DEPENDENCY, XT.GENERALIZATION, XT.REALIZATION, XT.USAGE]:
            for child in node.iter(tag):
                self._create_relationship(child)

        for child in node.iter(XT.ASSOCIATION):
            self._create_association(child)

    def _create_datatype(self, node: Et.Element) -> None:
        self._diagram.add_datatype(cd.Datatype(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node)
        ))

    def _create_class(self, node: Et.Element) -> None:
        self._diagram.add_datatype(cd.Class(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node),
            abstract=self._parse_abstract(node)
        ))

    def _create_stereotype(self, node: Et.Element) -> None:
        self._diagram.add_stereotype(cd.Stereotype(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node)
        ))

    def _create_relationship(self, node: Et.Element) -> None:
        try:
            relationship = cd.Relationship(
                identifier=self._parse_identifier(node),
                rel_type=self._parse_rel_type(node),
                from_cls=self._diagram.get_class(self._parse_identifier(node, attr=XA.FROM)),
                to_cls=self._diagram.get_class(self._parse_identifier(node, attr=XA.TO))
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
                from_cls=self._diagram.get_class(from_cls_id),
                to_cls=self._diagram.get_class(to_cls_id),
                from_mult=self._parse_mult(from_node),
                to_mult=self._parse_mult(to_node)
            )

            self._add_stereotypes(association, node)
            self._diagram.add_relationship(association)
        except Exception:
            return

    def _populate_class(self, node: Et.Element) -> None:
        cls = self._diagram.get_class(self._parse_identifier(node))
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
        method = cd.Method(
            identifier=self._parse_identifier(node),
            name=self._parse_name(node),
            scope=self._parse_scope(node),
            abstract=self._parse_abstract(node)
        )

        method.return_type = self._get_ref_datatype(node.find(XT.RET_TYPE))

        for child in node.iter(XT.PARAMETER):
            param = cd.Parameter(identifier=self._parse_identifier(child),
                                 name=self._parse_name(child),
                                 datatype=self._get_ref_datatype(child.find(XT.TYPE)))
            method.add_parameter(param)

        cls.methods.append(method)

    def _add_stereotypes(self, element: cd.StereotypedElement, node: Et.Element) -> None:
        for child in node.findall(XT.path(XT.STEREOTYPES, XT.STEREOTYPE)):
            stereotype = self._get_ref_stereotype(child)
            if stereotype:
                element.stereotypes.append(stereotype)

    def _get_ref_datatype(self, node: Et.Element) -> Optional[cd.Datatype]:
        try:
            return self._diagram.datatypes[self._parse_identifier(node[0], attr=XA.ID_REF)]
        except Exception:
            return None

    def _get_ref_stereotype(self, node: Et.Element) -> Optional[cd.Stereotype]:
        try:
            return self._diagram.stereotypes[self._parse_identifier(node, attr=XA.ID_REF)]
        except Exception:
            return None
