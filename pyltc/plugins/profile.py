"""
Profile plugin module.

Profile plugin allows for configuring command line setups within a config file
and later executing ``pyltc`` with that setup by just pointing to the profile
name (and optionally the profile configuration file location if not standard).

"""
import os

from pyltc.util.argsparse import parse_args, ArgParseError
from pyltc.util.confparser import ConfigParser
from pyltc.core.plug import PyltcPlugin


#: Default locations to look up the profiles config file if not specified
CONFIG_PATHS = (
    './pyltc.profiles',
    '/usr/local/etc/pyltc/profiles.conf',
    '/etc/pyltc/profiles.conf',
)


def determine_ini_conf_file():
    """Looks for (in pre-configured locations) and returns a profile config file
       if one is found or None if none has been found."""
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None  # explicitly


def parse_ini_file(profile, conf_file, verbose):
    """Parses given input file and returns a list of command line arguments
    equivalent to the settings of that profile.

    :param profile:
    :param conf_file:
    :param verbose:
    :return:
    """
    if not conf_file:
        conf_file = determine_ini_conf_file()

    if not conf_file:
        raise ArgParseError("Cannot find configuration filea after looking up in {}."
                            .format(CONFIG_PATHS))

    if verbose:
        print('Using config file {!r}'.format(conf_file))

    conf_parser = ConfigParser(conf_file)
    conf_parser.parse()

    try:
        new_args = conf_parser.section(profile)

    except KeyError:
        raise ArgParseError("Config profile NOT found: {}".format(profile))

    if verbose:
        print('Profile args:', new_args)

    return new_args


class ProfilePlugin(PyltcPlugin):
    """Plugin for handling config file profile discovery and application.

    (This plugin is part of the core pyltc distribution.)
    """

    __plugin_name__ = 'profile'

    @classmethod
    def add_subparser(cls, subparsers):
        subparser = subparsers.add_parser(cls.__plugin_name__,
                                          help="discover and apply profile configurations")

        subparser.add_argument('-v', '--verbose', action='store_true', required=False, default=False,
                                    help="more verbose output (default: %(default)s)")

        subparser.add_argument('-c', '--config', required=False, default=None,
                               help="profile configuration file to read from."
                                    " If not specified, default paths will be tried before giving up"
                                    " {}.".format(CONFIG_PATHS))

        subparser.add_argument('profile_name', help="profile name from the config file")
        return subparser

    def marshal(self):
        args = self._args
        # print("ARGS:", args)
        plugin_name = 'simnet'  # FIXME: determine real plugin name from profile name here!

        new_argv = parse_ini_file(args.profile_name, args.config, args.verbose)
        new_argv.insert(0, plugin_name)
        # old_args_dict = self._args.__dict__.copy()
        old_verbose = bool(self._args.verbose)
        new_args = parse_args(new_argv, old_verbose)

        PluginClass = PyltcPlugin.plugins_map.get(plugin_name)
        assert PluginClass, "cannot find plugin {!r}".format(args.subparser)

        plugin = PluginClass(new_args, self._target_factory)
        plugin.marshal()
