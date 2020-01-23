import sys

from . import cli, config


# Main


def main() -> int:
    try:
        ret_val = cli.process_args()
    except KeyboardInterrupt:
        print('Interrupted by user.', file=sys.stderr)
        ret_val = 1
    except Exception as e:
        if config.DEBUG:
            raise
        else:
            print(str(e), file=sys.stderr)
            ret_val = 1

    return ret_val
