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
import os
import argparse

from pyltc.conf import CONFIG_PATHS
from pyltc.util.confparser import ConfigParser


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
            cls.plugins.append(cls)
            assert cls.__plugin_name__ not in cls.plugins_map, \
                "Duplicate plugin name: {!r}".format(cls.__plugin_name__)
            cls.plugins_map[cls.__plugin_name__] = cls


def parse_args(argv, old_args_dict=None):
    """Parses given list of command line arguments using `argparse.ArgumentParser`
       and returns the parsed namespace."""
    # old_args_dict not None when we are called with profile; then it contains original profile args.
    old_args_dict = old_args_dict if old_args_dict else dict()
    parser = argparse.ArgumentParser(epilog="Use '%(prog)s sub-command -h/--help' to see the specific options.")

    if not argv:
        parser.error('Insufficient arguments. Try -h/--help.')

    if 'no_conf_file' in argv:
        parser.error('Cannot find configuration file - looked up in {}.'.format(CONFIG_PATHS))

    if 'no_such_profile' in argv:
        parser.error('Config profile NOT found: {}'.format(argv[1]))

    parser.add_argument('-V', '--version', action='store_true', help="show program version and exit")

    subparsers = parser.add_subparsers(dest='subparser')

    parser_profile = subparsers.add_parser('profile', help="profile to be used")

    parser_profile.add_argument('profile_name', help="profile name from the config file")

    parser_profile.add_argument('-v', '--verbose', action='store_true', required=False, default=False,
                                help="more verbose output (default: %(default)s)")

    parser_profile.add_argument('-c', '--config', required=False, default=None,
                                help="configuration file to read from."
                                     " If not specified, default paths will be tried before giving up"
                                     " (see module's CONFIG_PATHS).")

    for PluginClass in PyltcPlugin.plugins:
        PluginClass.add_subparser(subparsers)

    args = parser.parse_args(argv)
    args.verbose = args.verbose or old_args_dict.get('verbose', False)

    if not args.subparser:
        parser.error('No action requested.')

    PyltcPlugin.plugins_map[args.subparser].post_parse_process(args)
    return args


def determine_ini_conf_file():
    """Looks for (in pre-configured locations) and returns a profile config file
       if one is found or None if none has been found."""
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None  # explicitly


def parse_ini_file(profile, conf_file, verbose):
    """Parses given input file and returns a list of command line arguments
       equivalent to the settings of that profile."""
    if not conf_file:
        conf_file = determine_ini_conf_file()

    if not conf_file:  # FIXME: revisit this; raising an exception seems better
        return ['no_conf_file']

    if verbose:
        print('Using config file {!r}'.format(conf_file))

    conf_parser = ConfigParser(conf_file)
    conf_parser.parse()

    try:
        new_args = conf_parser.section(profile)
    except KeyError:  # FIXME: revisit this; raising an exception seems better
        return ['no_such_profile', '{!r}'.format(profile)]

    new_args.insert(0, 'simnet')  # FIXME: revisit this !!
    if verbose:
        print('Profile args:', new_args)
    return new_args


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
        if args and 'profile_name' in args:
            self.load_profile(args.profile_name, args.config)

    def load_profile(self, profile_name, config_file=None):
        profile_args = parse_ini_file(profile_name, config_file, self._args.verbose)
        old_args_dict = self._args.__dict__.copy()
        self._args = parse_args(profile_args, old_args_dict)

    def marshal(self):
        """TODO: docstring"""
        raise NotImplementedError('abstract method')
