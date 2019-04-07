from . import classdiagram as cd
from . import matcher as mt
from .parser import Parser
from .finder import PatternFinder


def create_diagram(file_path: str) -> cd.Diagram:
    return Parser().parse_document(file_path)


def create_matcher() -> mt.MultiMatcher:
    return mt.MultiMatcher(
        mt.AdapterMatcher(),
        mt.BridgeMatcher(),
        mt.CompositeMatcher(),
        mt.DecoratorMatcher(),
        mt.FacadeMatcher(),
        mt.ProxyMatcher()
    )


def create_finder(file_path: str) -> PatternFinder:
    diagram = create_diagram(file_path)
    return PatternFinder(diagram, create_matcher())
