"""
PyLTC plugins initialization.

We scan the ``pyltc/plugins`` directory and import any discovered packages
assuming them being PyLTC plugins.

"""
import os
from os.path import dirname, isfile, isdir, join as pjoin


__all__ = []

DEBUG = False
PLUGINS_PKG = 'pyltc.plugins'
EXPECTED_SKIPPED = {'__init__.py', '__pycache__'}


def print_if_debug(*args, **kw):
    if DEBUG:
        print(*args, **kw)


for _mod in os.listdir(dirname(__file__)):
    if isdir(pjoin(dirname(__file__), _mod)) and \
            isfile(pjoin(dirname(__file__), _mod, '__init__.py')):
        full_mod = "{}.{}".format(PLUGINS_PKG, _mod)
        __import__(full_mod, locals(), globals())
        __all__.append(_mod)
        print_if_debug("Added", full_mod)

    elif _mod[-3:] == '.py' and _mod != '__init__.py':
        full_mod = "{}.{}".format(PLUGINS_PKG, _mod[:-3])
        __import__(full_mod, locals(), globals())
        __all__.append(_mod[:-3])
        print_if_debug("Added", full_mod)

    else:
        if not _mod in EXPECTED_SKIPPED:
            print("WARNING: Skipped 'would-be' plugin entry:", _mod)


del _mod
