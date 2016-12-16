"""
The PyLTC main module.

This module will in the future take care of:

 (a) calling the parseargs stuff to make sure all common arguments
     are handled properly;

 (b) detect the plugin to be used, load it, parse its arguments
     and pass the settings to its entry point.

Currently we do not support plugins yet, so only (a) is done,
and for (b), the currently built-in thehunmonkgroup module is used.

"""
import sys

from pyltc.device import Interface
from pyltc.facade import TrafficControl
from pyltc.parseargs import handle_version_arg, parse_args, parse_ini_file
from pyltc.plugins import thehunmonkgroup


def pyltc_entry_point(argv=None):
    """
    Calls the parseargs stuff to make sure all common arguments
    are handled properly, then executes the default plugin entry point.

    :param argv: list - the command line arguments as provided by `sys.argv[1:]`
    :return: None
    """
    if not argv:
        argv = sys.argv[1:]

    handle_version_arg(argv)
    args = parse_args(argv)
    if args.verbose:
        print("Args:", str(args).lstrip("Namespace"))

    if 'profile_name' in args:
        profile_args = parse_ini_file(args.profile_name, args.config, args.verbose)
        old_args_dict = args.__dict__.copy()
        args = parse_args(profile_args, old_args_dict)

    TrafficControl.init()
    iface = TrafficControl.get_iface(args.iface)
    ifbdev = Interface.new_instance(args.ingress)  # returns a "Null" Interface object if args.ingress is None

    thehunmonkgroup.plugin_main(args, iface, ifbdev)
