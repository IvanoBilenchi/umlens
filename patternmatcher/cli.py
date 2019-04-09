import argparse

from . import config, controller

# Constants


EXE_NAME = 'matcher'
ALL_PATTERNS = controller.matchers.keys()


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
    main_parser.add_argument('-p', '--pattern',
                             choices=ALL_PATTERNS,
                             nargs='*',
                             help='Patterns to match.')
    main_parser.add_argument('-o', '--output',
                             help='Output file path.')

    main_parser.set_defaults(func=main_sub)

    return main_parser


# Subcommands


def main_sub(args) -> int:
    return controller.handle_args(args.input, output_path=args.output, patterns=args.pattern)
