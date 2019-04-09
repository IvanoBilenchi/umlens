import json
from itertools import groupby
from typing import Iterable

from .pattern import Pattern


class PatternJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Pattern):
            return {
                a: [str(i) for i in v] if isinstance(v, Iterable) else str(v)
                for a, v in o.__dict__.items()
            }

        return json.JSONEncoder.default(self, o)


def to_json(patterns: Iterable[Pattern], output_file: str) -> None:
    obj = dict((k, list(v)) for k, v in groupby(patterns, lambda p: p.name))

    with open(output_file, mode='w') as out:
        json.dump(obj, out, cls=PatternJSONEncoder, indent=2)


def to_stdout(patterns: Iterable[Pattern]) -> None:
    for pattern in sorted(patterns, key=lambda p: p.name):
        print(pattern)
