import json
from itertools import groupby
from typing import Iterable

from app.cycle.finder import Cycle
from app.metric.model import Metric
from app.pattern.model import Pattern


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Pattern):
            return {
                a: [str(i) for i in v] if isinstance(v, Iterable) else str(v)
                for a, v in o.__dict__.items()
            }
        elif isinstance(o, Cycle):
            return o.involved_classes
        elif hasattr(o, 'name'):
            return o.name

        return json.JSONEncoder.default(self, o)


def load(path: str):
    with open(path, "r") as json_file:
        return json.load(json_file)


def encode(obj, output_file: str) -> None:
    with open(output_file, mode='w') as out:
        json.dump(obj, out, cls=CustomJSONEncoder, indent=2)


def encode_patterns(patterns: Iterable[Pattern], output_file: str) -> None:
    obj = dict((k, list(v)) for k, v in groupby(patterns, lambda p: p.name))
    encode(obj, output_file)


def encode_cycles(cycles: Iterable[Cycle], output_file: str) -> None:
    encode_iterable(cycles, output_file)


def encode_metrics(metrics: Iterable[Metric], output_file: str) -> None:
    encode({m.identifier: m.value for m in metrics}, output_file)


def encode_iterable(iterable: Iterable, output_file: str) -> None:
    encode(list(iterable), output_file)
