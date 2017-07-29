"""
The PyLTC main module.

FIXME: Fix the documentation to reflect the latest plugin impl status:

This module will in the future take care of:

 (a) calling the parseargs stuff to make sure all common arguments
     are handled properly;

 (b) detect the plugin to be used, load it, parse its arguments
     and pass the settings to its entry point.

Currently we do not support plugins yet, so only (a) is done,
and for (b), the currently built-in ``simnet`` module is used.

"""
import os
import sys

from pyltc.conf import __version__, __build__
from pyltc.util.argsparse import parse_args, ArgParseError
from pyltc.core.facade import TrafficControl
from pyltc.core.plug import PyltcPlugin


def handle_version_arg(argv):
    """Handles the '--version' command line argument."""

    def compose_version():
        name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
        version_str = ".".join(map(str, __version__))
        return "{} verison {} (build {})".format(name, version_str, __build__)

    if '-V' in argv or '--version' in argv:
        print(compose_version())
        sys.exit(0)


def _main(argv, target_factory):
    if not argv:
        argv = sys.argv[1:]
    handle_version_arg(argv)
    args = parse_args(argv)
    if args.verbose:
        print("Args:", str(args).lstrip('Namespace'))

    PluginClass = PyltcPlugin.plugins_map.get(args.subparser)
    assert PluginClass, "cannot find plugin {!r}".format(args.subparser)

    plugin = PluginClass(args, target_factory)
    plugin.marshal()


def pyltc_entry_point(argv=None, target_factory=None):
    """
    Calls the parseargs stuff to make sure all common arguments
    are handled properly, then executes the default plugin entry point.

    :param argv: list - the command line arguments as provided by `sys.argv[1:]`
    :return: None
    """
    TrafficControl.init()

    try:
        _main(argv, target_factory)

    except ArgParseError as err:
        print("ltc.py: error:", err, file=sys.stderr)
        return 2


if __name__ == '__main__':
    pyltc_entry_point(['simnet', '-c', '--interface', 'lo', '-v', '--upload'])
