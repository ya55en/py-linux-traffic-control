"""
Command line arguments parsing utilities.

We intentionally keep the name of this module slightly different from
the standard library module ``argparse`` to avoid name collisions.

"""
import argparse
from pyltc.core.plug import PyltcPlugin


EPILOG = "Use '%(prog)s sub-command -h/--help' to see the specific options."


class ArgParseError(Exception):
    """Represents a command line parsing error condition."""


def parse_args(argv, old_verbose=None):
    """Parses given list of command line arguments using `argparse.ArgumentParser`
       and returns the parsed namespace."""
    # FIXME: remove next two lines when stable
    # old_args_dict not None when we are called with profile; then it contains original profile args.
    # old_args_dict = old_args_dict if old_args_dict else dict()
    parser = argparse.ArgumentParser(epilog=EPILOG)

    if not argv:
        parser.error('Insufficient arguments. Try -h/--help.')

    # FIXME: remove commented section when stable.
    # if 'no_conf_file' in argv:
    #     parser.error('Cannot find configuration file - looked up in {}.'.format(CONFIG_PATHS))
    #
    # if 'no_such_profile' in argv:
    #     parser.error('Config profile NOT found: {}'.format(argv[1]))

    parser.add_argument('-V', '--version', action='store_true', help="show program version and exit")

    subparsers = parser.add_subparsers(dest='subparser')
    for PluginClass in PyltcPlugin.plugins:
        PluginClass.add_subparser(subparsers)

    args = parser.parse_args(argv)
    args.verbose = args.verbose or old_verbose

    if not args.subparser:
        parser.error('No action requested.')

    PyltcPlugin.plugins_map[args.subparser].post_parse_process(args)
    return args
