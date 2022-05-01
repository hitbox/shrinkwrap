from . import cut
from . import query

def init_subparsers(subparsers):
    """
    Initialize sub-commands/parsers
    """
    sp = subparsers.add_parser('cut', prog='cut', help=cut.run.__doc__)
    cut.init_parser(sp)

    sp = subparsers.add_parser('query', prog='query', help=query.run.__doc__)
    query.init_parser(sp)