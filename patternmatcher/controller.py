from importlib import import_module
from typing import Optional

from . import encoder, pattern
from .factory import AppFactory

_matcher_module = import_module('.matcher', 'patternmatcher')

matchers = dict(zip(
    [p.__name__.lower() for p in pattern.ALL],
    [getattr(_matcher_module, p.__name__ + 'Matcher') for p in pattern.ALL]
))


def handle_args(input_path: str, output_path: Optional[str] = None,
                patterns: Optional[str] = None) -> int:

    enabled_matchers = [matchers[p] for p in patterns] if patterns else matchers.values()
    patterns = AppFactory().create_finder(input_path, enabled_matchers).get_patterns()

    if output_path:
        encoder.to_json(patterns, output_path)
    else:
        encoder.to_stdout(patterns)

    return 0
