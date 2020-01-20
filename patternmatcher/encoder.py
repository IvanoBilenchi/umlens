import json
from itertools import groupby
from typing import Iterable

from .pattern import Pattern
from .finder import CycleInfo
from .stats import Stats


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Pattern):
            return {
                a: [str(i) for i in v] if isinstance(v, Iterable) else str(v)
                for a, v in o.__dict__.items()
            }
        elif isinstance(o, CycleInfo):
            return {
                'hierarchy': list(sorted(o.hierarchy)),
                'count': o.count
            }
        elif isinstance(o, Stats):
            return {k: getattr(o, k)() for k in (
                'packages', 'classes', 'pattern_types', 'classes_in_pattern',
                'classes_not_in_pattern', 'classes_in_pattern_ratio',
                'avg_methods_per_class', 'avg_relationships_per_class', 'dependency_cycles'
            )}
        elif hasattr(o, 'name'):
            return o.name

        return json.JSONEncoder.default(self, o)


def patterns_to_json(patterns: Iterable[Pattern], output_file: str) -> None:
    obj = dict((k, list(v)) for k, v in groupby(patterns, lambda p: p.name))
    to_json(obj, output_file)


def cycles_to_json(cycles: Iterable[CycleInfo], output_file: str) -> None:
    to_json(list(cycles), output_file)


def stats_to_json(stats: Stats, output_file: str) -> None:
    to_json(stats, output_file)


def to_json(obj, output_file: str) -> None:
    with open(output_file, mode='w') as out:
        json.dump(obj, out, cls=CustomJSONEncoder, indent=2)
