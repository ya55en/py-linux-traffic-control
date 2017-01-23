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

from pyltc.core.facade import TrafficControl
from pyltc.plugins import simnet
from parser import ParserError


def pyltc_entry_point(argv=None, target_factory=None):
    """
    Calls the parseargs stuff to make sure all common arguments
    are handled properly, then executes the default plugin entry point.

    :param argv: list - the command line arguments as provided by `sys.argv[1:]`
    :return: None
    """
    TrafficControl.init()
    try:
        simnet.plugin_main(argv, target_factory)
    except ParserError as err:
        print("ltc.py: error:", err, file=sys.stderr)
        return 2
