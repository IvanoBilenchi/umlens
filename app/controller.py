from typing import Optional

from .uml import json
from .uml.matcher import Matcher

from .factory import AppFactory

matchers = {p.__name__.lower(): m for p, m in Matcher.all().items()}


def detect_patterns(input_path: str, output_path: Optional[str] = None,
                    patterns: Optional[str] = None) -> int:
    enabled_matchers = (matchers[p] for p in patterns) if patterns else matchers.values()
    patterns = AppFactory(input_path).create_pattern_finder(enabled_matchers).patterns()

    if output_path:
        json.encode_patterns(patterns, output_path)
    else:
        for pattern in sorted(patterns):
            print(pattern)

    return 0


def detect_cycles(input_path: str, output_path: Optional[str] = None) -> int:
    finder = AppFactory(input_path).create_cycle_finder()
    cycles = finder.cycles()

    if output_path:
        json.encode_cycles(cycles, output_path)
    else:
        print('Dependency cycles: {}'.format(finder.cycle_count()))
        for cycle in sorted(cycles):
            print(cycle)

    return 0


def compute_metrics(diagram_path: str, config_path: Optional[str] = None,
                    output_path: Optional[str] = None) -> int:
    metrics = AppFactory(diagram_path, config_path=config_path).create_metrics()

    if output_path:
        json.encode_metrics(metrics, output_path)
    else:
        for metric in metrics:
            print(metric)

    return 0
