from typing import Optional

from . import encoder
from .factory import AppFactory
from .matcher import Matcher


matchers = {p.__name__.lower(): m for p, m in Matcher.all().items()}


def detect_patterns(input_path: str, output_path: Optional[str] = None,
                    patterns: Optional[str] = None) -> int:
    enabled_matchers = (matchers[p] for p in patterns) if patterns else matchers.values()
    patterns = AppFactory().create_pattern_finder(input_path, enabled_matchers).patterns()

    if output_path:
        encoder.patterns_to_json(patterns, output_path)
    else:
        for pattern in sorted(patterns):
            print(pattern)

    return 0


def detect_cycles(input_path: str, output_path: Optional[str] = None) -> int:
    finder = AppFactory().create_cycle_finder(input_path)
    cycles = finder.cycles()

    if output_path:
        encoder.cycles_to_json(cycles, output_path)
    else:
        print('Cycles: {}'.format(finder.cycle_count()))
        for cycle in sorted(cycles):
            print(cycle)

    return 0


def print_info(input_path: str, output_path: Optional[str] = None) -> int:
    stats = AppFactory().create_stats(input_path)

    if output_path:
        encoder.stats_to_json(stats, output_path)
    else:
        print(stats)

    return 0
