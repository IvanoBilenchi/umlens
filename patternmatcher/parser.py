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
    NAME = 'Name'
    SCOPE = 'Scope'
    TO = 'To'


class Parser:

    def __init__(self) -> None:
        self._diagram = cd.Diagram()

    def parse_document(self, file_path: str) -> cd.Diagram:
        node: Et.Element = Et.parse(file_path).getroot().find(XT.MODELS)
        self.parse_datatypes(node)

        node = node.find(XT.path(XT.MODEL_RELATIONSHIP_CONTAINER, XT.MODEL_CHILDREN))
        self.parse_relationships(node)

        return self._diagram

    def parse_datatypes(self, node: Et.Element) -> None:
        for model in node.findall(XT.STEREOTYPE):
            self.create_stereotype(model)

        for model in node.findall(XT.DATATYPE):
            self.create_datatype(model)

        for model in node.findall(XT.CLASS):
            self.create_class(model)

        for model in node.findall(XT.CLASS):
            self.populate_class(model)

    def parse_relationships(self, node: Et.Element) -> None:
        for tag in [XT.DEPENDENCY, XT.GENERALIZATION, XT.REALIZATION, XT.USAGE]:
            for child in node.iter(tag):
                self.create_relationship(child)

        for child in node.iter(XT.ASSOCIATION):
            self.create_association(child)

    def create_datatype(self, node: Et.Element) -> None:
        self._diagram.add_datatype(cd.Datatype(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node)
        ))

    def create_class(self, node: Et.Element) -> None:
        self._diagram.add_datatype(cd.Class(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node),
            abstract=self.parse_abstract(node)
        ))

    def create_stereotype(self, node: Et.Element) -> None:
        self._diagram.add_stereotype(cd.Stereotype(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node)
        ))

    def create_relationship(self, node: Et.Element) -> None:
        try:
            relationship = cd.Relationship(
                identifier=self.parse_identifier(node),
                rel_type=self.parse_rel_type(node),
                from_cls=self._diagram.get_class(self.parse_identifier(node, attr=XA.FROM)),
                to_cls=self._diagram.get_class(self.parse_identifier(node, attr=XA.TO))
            )

            self.add_stereotypes(relationship, node)
            self._diagram.add_relationship(relationship)
        except Exception:
            return

    def create_association(self, node: Et.Element) -> None:
        try:
            from_node = node.find(XT.path(XT.FROM_END, XT.ASSOCIATION_END))
            to_node = node.find(XT.path(XT.TO_END, XT.ASSOCIATION_END))

            from_cls_id = self.parse_identifier(from_node, attr=XA.END_MODEL_ELEMENT)
            to_cls_id = self.parse_identifier(to_node, attr=XA.END_MODEL_ELEMENT)

            association = cd.Association(
                identifier=self.parse_identifier(node),
                agg_type=self.parse_agg_type(from_node),
                from_cls=self._diagram.get_class(from_cls_id),
                to_cls=self._diagram.get_class(to_cls_id)
            )

            self.add_stereotypes(association, node)
            self._diagram.add_relationship(association)
        except Exception:
            return

    def populate_class(self, node: Et.Element) -> None:
        cls = self._diagram.get_class(self.parse_identifier(node))
        ch_node = node.find(XT.MODEL_CHILDREN)

        if ch_node:
            for child in ch_node.findall(XT.ATTRIBUTE):
                self.add_attribute(cls, child)

            for child in ch_node.findall(XT.OPERATION):
                self.add_method(cls, child)

        self.add_stereotypes(cls, node)

    def add_attribute(self, cls: cd.Class, node: Et.Element) -> None:
        attr = cd.Attribute(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node),
            datatype=self.parse_type(node, XT.TYPE),
            scope=self.parse_scope(node)
        )
        cls.attributes.append(attr)

    def add_method(self, cls: cd.Class, node: Et.Element) -> None:
        method = cd.Method(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node),
            scope=self.parse_scope(node),
            abstract=self.parse_abstract(node)
        )

        method.return_type = self.parse_type(node, XT.RET_TYPE)

        for child in node.iter(XT.PARAMETER):
            param = cd.Parameter(identifier=self.parse_identifier(child),
                                 name=self.parse_name(child),
                                 datatype=self.parse_type(child, XT.TYPE))
            method.add_parameter(param)

        cls.methods.append(method)

    def add_stereotypes(self, element: cd.StereotypedElement, node: Et.Element) -> None:
        for child in node.findall(XT.path(XT.STEREOTYPES, XT.STEREOTYPE)):
            stereotype = self.parse_stereotype(child)
            if stereotype:
                element.stereotypes.append(stereotype)

    @staticmethod
    def parse_identifier(node: Et.Element, attr: str = XA.ID) -> str:
        try:
            return node.attrib[attr]
        except Exception as e:
            raise Exception('Node has no identifier: {} {}'.format(node.tag, node.attrib)) from e

    @staticmethod
    def parse_name(node: Et.Element) -> str:
        return node.attrib.get(XA.NAME, '')

    @staticmethod
    def parse_abstract(node: Et.Element) -> bool:
        return node.attrib.get(XA.ABSTRACT, 'false') == 'true'

    @staticmethod
    def parse_scope(node: Et.Element) -> cd.Scope:
        return cd.Scope.INSTANCE if node.attrib.get(XA.SCOPE, 'instance') else cd.Scope.CLASS

    @staticmethod
    def parse_rel_type(node: Et.Element) -> Optional[cd.RelationshipType]:
        try:
            return cd.RelationshipType[node.tag.upper()]
        except Exception:
            if node.tag == XT.USAGE:
                return cd.RelationshipType.DEPENDENCY
            raise

    @staticmethod
    def parse_agg_type(node: Et.Element) -> cd.AggregationType:
        try:
            return cd.AggregationType[node.attrib[XA.AGGREGATION_KIND].upper()]
        except Exception:
            return cd.AggregationType.NONE

    def parse_type(self, node: Et.Element, container: str) -> Optional[cd.Datatype]:
        try:
            return self._diagram.datatypes[node.find(container)[0].attrib[XA.ID_REF]]
        except Exception:
            return None

    def parse_stereotype(self, node: Et.Element) -> Optional[cd.Stereotype]:
        try:
            return self._diagram.stereotypes[node.attrib[XA.ID_REF]]
        except Exception:
            return None
