import argparse

from . import commands

def main(argv=None):
    """
    Demo lib operations
    """
    parser = argparse.ArgumentParser(
        description = main.__doc__,
    )
    subparsers = parser.add_subparsers()
    commands.init_subparsers(subparsers)
    args = parser.parse_args(argv)

    func = args.func
    del args.func
    func(args)
