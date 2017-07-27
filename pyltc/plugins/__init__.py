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
        _mod = "pyltc.plugins.{}".format(_mod)
        __import__(_mod, locals(), globals())
        __all__.append(_mod)
        print("Added", _mod)

    elif _mod[-3:] == '.py' and _mod != '__init__.py':
        __import__(_mod[:-3], locals(), globals())
        __all__.append(_mod[:-3])
        print("Added", _mod[:-3])

    else:
        print("Skipped plugin entry:", _mod)


del _mod
