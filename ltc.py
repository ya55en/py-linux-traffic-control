#! /usr/bin/env python3
"""
'Executable' for the PyLTC command line.

"""
import sys


if __name__ != '__main__':
    raise RuntimeError("Do NOT import {}, execute it".format(sys.argv[0]))


from os.path import abspath, normpath, dirname

HOME_DIR = normpath(abspath(dirname(__file__)))
if HOME_DIR not in sys.path:
    sys.path.insert(0, HOME_DIR)

from pyltc.main import pyltc_entry_point
sys.exit(pyltc_entry_point(sys.argv[1:]))
