"""
PyLTC plugins initialization.

We scan the ``pyltc/plugins`` directory and import any discovered packages.

"""
import os
from os.path import dirname, isfile, isdir, join as pjoin


__all__ = []


for _mod in os.listdir(dirname(__file__)):
    if isdir(pjoin(dirname(__file__), _mod)) and \
            isfile(pjoin(dirname(__file__), _mod, '__init__.py')):
        full_mod = "pyltc.plugins.{}".format(_mod)
        __import__(full_mod, locals(), globals())
        __all__.append(_mod)
        print("Added", full_mod)

    elif _mod[-3:] == '.py' and _mod != '__init__.py':
        full_mod = "pyltc.plugins.{}".format(_mod[:-3])
        __import__(full_mod, locals(), globals())
        __all__.append(_mod[:-3])
        print("Added", full_mod)

    else:
        print("Skipped plugin entry:", _mod)


del _mod
