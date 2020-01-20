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

    # IO parser
    io_parser = argparse.ArgumentParser(add_help=False)

    group = io_parser.add_argument_group('Input/Output')
    group.add_argument('-i', '--input',
                       help='Input document.',
                       required=True)
    group.add_argument('-o', '--output',
                       help='Output file path.')

    # Main parser
    main_parser = argparse.ArgumentParser(prog=EXE_NAME,
                                          description='Detects design patterns in class diagrams.',
                                          parents=[help_parser],
                                          add_help=False)

    subparsers = main_parser.add_subparsers(title='Subcommands')

    # 'patterns' subcommand
    description = 'List detected design patterns.'
    patterns_parser = subparsers.add_parser('patterns',
                                            description=description,
                                            help=description,
                                            parents=[help_parser, io_parser],
                                            add_help=False)
    patterns_parser.add_argument('-p', '--pattern',
                                 choices=ALL_PATTERNS,
                                 nargs='*',
                                 help='Patterns to match.')
    patterns_parser.set_defaults(func=patterns_sub)

    # 'cycles' subcommand
    description = 'List detected dependency cycles.'
    info_parser = subparsers.add_parser('cycles',
                                        description=description,
                                        help=description,
                                        parents=[help_parser, io_parser],
                                        add_help=False)
    info_parser.set_defaults(func=cycles_sub)

    # 'info' subcommand
    description = 'Print miscellaneous information and stats.'
    info_parser = subparsers.add_parser('info',
                                        description=description,
                                        help=description,
                                        parents=[help_parser, io_parser],
                                        add_help=False)
    info_parser.set_defaults(func=info_sub)

    return main_parser


# Subcommands


def patterns_sub(args) -> int:
    return controller.detect_patterns(args.input, output_path=args.output, patterns=args.pattern)


def cycles_sub(args) -> int:
    return controller.detect_cycles(args.input, output_path=args.output)


def info_sub(args) -> int:
    return controller.print_info(args.input, output_path=args.output)
