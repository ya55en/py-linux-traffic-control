"""
PyLTC command line argument parsing module.

"""

import os
import sys
import argparse

from pyltc.conf import CONFIG_PATHS, __version__, __build__
from pyltc.util.cmdline import CommandLine
from pyltc.util.confparser import ConfigParser


class MisconfigurationError(Exception):
    """Represents an error in command line or profile setup."""
    # FIXME: rename to something like IllegalArguments


def determine_ini_conf_file():
    """Looks for in preconfigured locations and returns a profile config file
       if one is found or None if none has been found."""
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None  # explicitly


def parse_ini_file(profile, conf_file, verbose):
    """Parses given input file and returns a list of command line arguments
       equivalent to that profile."""
    if not conf_file:
        conf_file = determine_ini_conf_file()
    if not conf_file:   # FIXME: revisit this; raising an exception seems better
        return ['no_conf_file']
    if verbose:
        print('Using config file {!r}'.format(conf_file))

    conf_parser = ConfigParser(conf_file)
    conf_parser.parse()
    try:
        new_args = conf_parser.section(profile)
    except KeyError:    # FIXME: revisit this; raising an exception seems better
        return ['no_such_profile', '{!r}'.format(profile)]

    new_args.insert(0, 'tc')
    print(new_args)
    return new_args


def parse_args(argv):
    """Parses given list of command line arguments using `argparse.ArgumentParser`
       and returns the parsed namespace."""
    parser = argparse.ArgumentParser(epilog="Use '%(prog)s subcommand -h/--help' to see the specific options.")
    if not argv:
        parser.error('Insufficient arguments. Try -h/--help.')
    if 'no_conf_file' in argv:
        parser.error('Cannot find configuration file (looked up in {}).'.format(CONFIG_PATHS))
    if 'no_such_profile' in argv:
        parser.error('No such profile found: {}'.format(argv[1]))
    parser.add_argument("-V", "--version", action='store_true', help="show program version and exit")

    subparsers = parser.add_subparsers(dest="subparser")
    #parser_versioin = subparsers.add_parser("--version", help="Show program version and exit.")
    parser_profile = subparsers.add_parser("profile", help="profile to be used")
    parser_profile.add_argument("profile_name", help="profile name from the config file")
    parser_profile.add_argument("-v", "--verbose", action='store_true', required=False, default=False,
                        help="more verbose output (default: %(default)s)")
    parser_profile.add_argument("-c", "--config", required=False, default=None,
                                help="configuration file to read from."
                                " If not specified, default paths will be tried before giving up"
                                " (see module's CONFIG_PATHS).")

    parser_cmd = subparsers.add_parser("tc", help="traffc control setup to be applied")
    parser_cmd.add_argument("-v", "--verbose", action='store_true', required=False, default=False,
                            help="more verbose output (default: %(default)s)")
    parser_cmd.add_argument("-i", "--iface", required=False, default='lo',
                            help="the network device name (default: %(default)s)")
    parser_cmd.add_argument("-c", "--clear", action='store_true', required=False, default=False,
                            help="generate a chain clearing clause before the actual recipe"
                                 " (default: %(default)s)")
    parser_cmd.add_argument("-in", "--ingress", required=False, default=None,
                            help="defined ingress control, specifying which ifb device to use;"
                                 " 'setup' means setting up a new ifb device"
                                 " (default: %(default)s)")
    parser_cmd.add_argument("-dc", "--dclass", default=None, action='append',
                            metavar='PROTOCOL:RANGE:RATE:JITTER',
                            help="Define a discipline class for dest port range. Example:"
                                 " udp:21-24:256kbit:10%%. RANGE is required."
                                 " RATE and/or JITTER must be present. PROTOCOL is one of 'tcp', 'udp'"
                                 " (default: 'tcp').")
    parser_cmd.add_argument("-sc", "--sclass", default=None, action='append',
                            metavar='PROTOCOL:RANGE:RATE:JITTER',
                            help="Define a discipline class for source port range. Example:"
                                 " tcp:16000-24000:512kbit:5%%. RANGE is required."
                                 " RATE and/or JITTER must be present. PROTOCOL is one of 'tcp', 'udp'"
                                 " (default: 'tcp').")

    args = parser.parse_args(argv)
    if not args.subparser:
        parser.error('No action requested.')

    args.ingress = handle_ingress_arg(args.ingress, parser)

    if args.subparser == 'tc' and not (args.sclass or args.dclass or args.clear):
        parser.error('No action requested: add at least one of --sclass, --dclass, --clear.')
    return args


def handle_ingress_arg(ingress_arg, parser):
    if not ingress_arg:
        return None
    available_ifs = os.listdir('/sys/class/net/')
    available_ibfs = sorted((iface for iface in available_ifs if iface.startswith('ifb')))
    if ingress_arg in available_ibfs:
        return ingress_arg  # using an existing and preconfigured ifb device
    if ingress_arg != 'setup':
        parser.error("ifb device not found: {!r}. Use 'setup' to set up a new one.".format(ingress_arg))
    # we need to set up a new device
    if not available_ibfs:
        CommandLine('modprobe --remove ifb').execute()
        CommandLine('modprobe ifb numifbs=1').execute()
        CommandLine('ip link set dev ifb0 up').execute()
        available_ifs = os.listdir('/sys/class/net/')
        available_ibfs = sorted((iface for iface in available_ifs if iface.startswith('ifb')))
        assert len(available_ibfs) == 1, "expected available_ibfs to have single element, got {!r}" \
                                          .format(available_ibfs)
        return available_ibfs[0]

    ifbnum = [int(el.lstrip('ifb')) for el in available_ibfs][-1] + 1
    ifbdev = "ifb{}".format(ifbnum)
    CommandLine('ip link add {} type ifb'.format(ifbdev)).execute()
    CommandLine('ip link set dev {} up'.format(ifbdev)).execute()
    return ifbdev


def handle_version_arg(argv):
    """Handles the version command line argument."""

    def compose_version():
        name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
        version_str = ".".join(map(str, __version__))
        #maintainer = __maintainer__.replace("-at-", "@")
        return "{} verison {} (build {})".format(name, version_str, __build__)

    if '-V' in argv or '--version' in argv:
        print(compose_version())
        sys.exit(0)
