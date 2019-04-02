import xml.etree.ElementTree as Et
from typing import Optional

from . import classdiagram as cd


class XT:
    """XML tags namespace."""
    ATTRIBUTE = 'Attribute'
    CLASS = 'Class'
    DATATYPE = 'DataType'
    MODEL_CHILDREN = 'ModelChildren'
    MODELS = 'Models'
    OPERATION = 'Operation'
    PARAMETER = 'Parameter'
    RET_TYPE = 'ReturnType'
    STEREOTYPE = 'Stereotype'
    STEREOTYPES = 'Stereotypes'
    TYPE = 'Type'


class XA:
    """XML attributes namespace."""
    ABSTRACT = 'Abstract'
    ID = 'Id'
    ID_REF = 'Idref'
    NAME = 'Name'
    SCOPE = 'Scope'


class Parser:

    def __init__(self) -> None:
        self.diagram = cd.Diagram()

        self.class_child_handlers = {
            XT.ATTRIBUTE: self.add_attribute,
            XT.OPERATION: self.add_method
        }

    def parse_document(self, file_path: str) -> cd.Diagram:
        tree = Et.parse(file_path)
        models: Et.Element = tree.getroot().find(XT.MODELS)

        for model in models.findall(XT.STEREOTYPE):
            self.create_stereotype(model)

        for model in models.findall(XT.DATATYPE):
            self.create_datatype(model)

        for model in models.findall(XT.CLASS):
            self.create_class(model)

        for model in models.findall(XT.CLASS):
            self.populate_class(model)

        return self.diagram

    def create_datatype(self, node: Et.Element) -> None:
        self.diagram.add_datatype(cd.Datatype(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node)
        ))

    def create_class(self, node: Et.Element) -> None:
        self.diagram.add_datatype(cd.Class(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node),
            abstract=self.parse_abstract(node)
        ))

    def create_stereotype(self, node: Et.Element) -> None:
        self.diagram.add_stereotype(cd.Stereotype(
            identifier=self.parse_identifier(node),
            name=self.parse_name(node)
        ))

    def populate_class(self, node: Et.Element) -> None:
        cls = self.diagram.get_class(self.parse_identifier(node))
        ch_node = node.find(XT.MODEL_CHILDREN)

        if ch_node:
            for child in ch_node.findall(XT.ATTRIBUTE):
                self.add_attribute(cls, child)

            for child in ch_node.findall(XT.OPERATION):
                self.add_method(cls, child)

        ch_node = node.find(XT.STEREOTYPES)

        if ch_node:
            for child in ch_node.findall(XT.STEREOTYPE):
                self.add_stereotype(cls, child)

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

    def add_stereotype(self, cls: cd.Class, node: Et.Element) -> None:
        stereotype = self.parse_stereotype(node)
        if stereotype:
            cls.stereotypes.append(stereotype)

    @staticmethod
    def parse_identifier(node: Et.Element) -> str:
        try:
            return node.attrib[XA.ID]
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

    def parse_type(self, node: Et.Element, container: str) -> Optional[cd.Datatype]:
        try:
            return self.diagram.datatypes[node.find(container)[0].attrib[XA.ID_REF]]
        except Exception:
            return None

    def parse_stereotype(self, node: Et.Element) -> Optional[cd.Stereotype]:
        try:
            return self.diagram.stereotypes[node.attrib[XA.ID_REF]]
        except Exception:
            return None
