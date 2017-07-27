"""
PyLTC plugins directory.

"""
from os.path import abspath, normpath, dirname, basename, isfile, isdir, join as pjoin


import os

__all__ = []

for mod_ in os.listdir(dirname(__file__)):
    if isdir(pjoin(dirname(__file__), mod_)) and \
            isfile(pjoin(dirname(__file__), mod_, '__init__.py')):
        mod_ = "pyltc.plugins.{}".format(mod_)
        __import__(mod_, locals(), globals())
        __all__.append(mod_)

    elif mod_[-3:] == '.py' and mod_ != '__init__.py':
        __import__(mod_[:-3], locals(), globals())
        __all__.append(mod_[:-3])

    else:
        print("Skipped plugin entry:", mod_)


del mod_

print(__all__)
