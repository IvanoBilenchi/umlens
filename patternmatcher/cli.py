import argparse

from . import classdiagram as cd, config
from .parser import Parser

# Constants


EXE_NAME = 'matcher'


# CLI parser


def process_args() -> int:
    """Runs actions based on CLI arguments."""
    args = build_parser().parse_args()

    if args.debug:
        config.DEBUG = True

    if not hasattr(args, 'func'):
        msg = ('Invalid argument(s). Please run "{0} -h" for help.'.format(EXE_NAME))
        raise ValueError(msg)

    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the CLI parser."""

    # Help parser
    help_parser = argparse.ArgumentParser(add_help=False)

    group = help_parser.add_argument_group('Help and debug')
    group.add_argument('--debug',
                       help='Enable debug output.',
                       action='store_true')
    group.add_argument('-h', '--help',
                       help='Show this help message and exit.',
                       action='help')

    # Main parser
    main_parser = argparse.ArgumentParser(prog=EXE_NAME,
                                          description='Detects design patterns in class diagrams.',
                                          parents=[help_parser],
                                          add_help=False)

    main_parser.add_argument('input',
                             help='Input document.')
    main_parser.add_argument('-o', '--output',
                             help='Output file path.')

    main_parser.set_defaults(func=main_sub)

    return main_parser


# Subcommands


def main_sub(args) -> int:
    diagram = Parser().parse_document(args.input)

    print(diagram)

    print('\nRelated classes:\n----------------')

    for cls in sorted(diagram.get_classes()):
        sub = diagram.get_related_classes(cls, role=cd.RelRole.RHS)
        print('{}: {}'.format(cls.name, ', '.join(c.name for c in sorted(sub))))

    return 0
