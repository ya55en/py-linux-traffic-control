"""
PyLTC simple plugin framework.

Based on Marty Alchin's Simple Plugin Framework at
  http://martyalchin.com/2008/jan/10/simple-plugin-framework/


Directions for plugin developers:
---------------------------------

To write a compatible PyLTC plugin, you need to:

1. Provide the plugin in the form of a package installed within ``pyltc.plugins``.

2. Make sure your plugin package has a directly importable ``PyltcPlugin``
   subclass (e.g. ``my_plugin.MyPyltcPlugin``).

3. Your `PyltcPlugin`` subclass needs to provide correct implementations of all
   ``PyltcPlugin`` abstract methods, namely:
   - ``get_args_parser()``
   - ``marshall()``.

That's it ;)

Please refer to the ``simreg`` plugin for a sample implementation.
"""
import argparse


class PluginMountMeta(type):
    """
    Metaclass for the ``PyltcPlugin`` subclasses.

    This class creates a simple classes registry for a base class (e.g.
    ``PyltcPlugin``) and then adds each new sub-class of the base class
    to that registry thus making all plugins accessible to the core
    pyltc framework without the need for the latter to know what plugins
    are actually installed.
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = list()
            cls.plugins_map = dict()

        else:
            assert cls.__plugin_name__, \
                "plugin {!r} has no __plugin_name__".format(name)
            assert cls.__plugin_name__ not in cls.plugins_map, \
                "Duplicate plugin name: {!r}".format(cls.__plugin_name__)

            cls.plugins.append(cls)
            cls.plugins_map[cls.__plugin_name__] = cls


class PyltcPlugin(metaclass=PluginMountMeta):
    """
    Base class and "mount point" for any PyLTC plugins.

    Subclass implementing all abstract methods to provide a new plugin.
    """

    __plugin_name__ = None

    @classmethod
    def add_subparser(cls, subparsers):
        """TODO: docstring"""
        raise NotImplementedError('abstract method')

    @classmethod
    def post_parse_process(cls, args):
        """Processing command line args after initial parsing, if needed (may
        modify args in-place). Default implementation does nothing.

        :param args: Namespace - command line arguments namespace
        """

    def __init__(self, args=None, target_factory=None):
        """Initializer.
        :param args: parser.Namespace - the command line arguments
        :param target_factory: callable returning the target factory
               to create the target chain builders with
        """
        self._target_factory = target_factory
        self._args = args

    def marshal(self):
        """TODO: docstring"""
        raise NotImplementedError('abstract method')
