"""
Chad Phillips' (thehunmonkgroup) network simulation plugin.

Note that this NOT yet converted to an actual plugin but rather imported
as a Python module currently.

TODO: introduce plugin functionality and convert this to be the first plugin ;)
      (This has been partially done with introducing the ``SimNetPlugin`` class.)

"""

import os
import sys
import argparse

from pyltc.conf import CONFIG_PATHS, __build__, __version__
from parser import ParserError
from pyltc.util.cmdline import CommandLine
from pyltc.util.confparser import ConfigParser
from pyltc.core.netdevice import DeviceManager, NetDevice
from pyltc.plugins.util import parse_branch

#: netem (the qdisc that simulates special network conditions) works for a
# default of 1000 packets. This was a source of problems and the workaround
# that I came up with currently is to set it to a very large  number.
#: Chad: Beware that if you keep that filter on for too long, this limit may
# be reached.
NETEM_LIMIT = 1000000000


class IllegalArguments(Exception):
    """Represents an error in command line or profile setup."""


def determine_ini_conf_file():
    """Looks for (in preconfigured locations) and returns a profile config file
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

    new_args.insert(0, 'tc')
    if verbose:
        print("Profile args:", new_args)
    return new_args


def determine_ifb_device(ifbdevice_arg, verbose_arg, parser):
    """Returns the name of the ifb device while handling the '--download' command line
    argument (denoting ingress traffic control). Reuses an existing device if specified
    and available or create a new device as necessary.
    """
    if not ifbdevice_arg:
        return None
    available_ifbs = sorted(DeviceManager.all_iface_names(filter='ifb'))
    if ifbdevice_arg in available_ifbs:
        return ifbdevice_arg  # using an existing and preconfigured ifb device
    if ifbdevice_arg != 'setup':
        parser.error(
            "ifb device not found: {!r}. Leave '--ifbdevice' switch empty to set up a new one.".format(ifbdevice_arg))
        raise RuntimeError('UNREACHABLE')

    # we need to set up a new device
    if not available_ifbs:
        CommandLine('modprobe ifb numifbs=0', verbose=verbose_arg, sudo=True).execute()
        CommandLine('ip link add ifb0 type ifb', verbose=verbose_arg, sudo=True).execute()
        CommandLine('ip link set dev ifb0 up', verbose=verbose_arg, sudo=True).execute()
        available_ifbs = sorted(DeviceManager.all_iface_names(filter='ifb'))
        assert len(available_ifbs) == 1, "expected available_ifbs to have single device, got {!r}" \
                                          .format(available_ifbs)

    ifbnum = [int(el.lstrip('ifb')) for el in available_ifbs][-1]  # + 1
    ifbdev = "ifb{}".format(ifbnum)
    CommandLine('ip link set dev {} up'.format(ifbdev), verbose=verbose_arg, sudo=True).execute()
    return ifbdev


def handle_version_arg(argv):
    """Handles the '--version' command line argument."""

    def compose_version():
        name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
        version_str = ".".join(map(str, __version__))
        return "{} verison {} (build {})".format(name, version_str, __build__)

    if '-V' in argv or '--version' in argv:
        print(compose_version())
        sys.exit(0)


def parse_args(argv, old_args_dict=None):
    """Parses given list of command line arguments using `argparse.ArgumentParser`
       and returns the parsed namespace."""
    old_args_dict = old_args_dict if old_args_dict else dict()
    parser = argparse.ArgumentParser(epilog="Use '%(prog)s subcommand -h/--help' to see the specific options.")
    if not argv:
        parser.error('Insufficient arguments. Try -h/--help.')
    if 'no_conf_file' in argv:
        parser.error('Cannot find configuration file - looked up in {}.'.format(CONFIG_PATHS))
    if 'no_such_profile' in argv:
        parser.error('No such profile found: {}'.format(argv[1]))
    parser.add_argument("-V", "--version", action='store_true', help="show program version and exit")

    subparsers = parser.add_subparsers(dest="subparser")
    parser_profile = subparsers.add_parser("profile", help="profile to be used")
    parser_profile.add_argument("profile_name", help="profile name from the config file")
    parser_profile.add_argument("-v", "--verbose", action='store_true', required=False, default=False,
                                help="more verbose output (default: %(default)s)")
    parser_profile.add_argument("-c", "--config", required=False, default=None,
                                help="configuration file to read from."
                                     " If not specified, default paths will be tried before giving up"
                                     " (see module's CONFIG_PATHS).")

    parser_cmd = subparsers.add_parser("tc", help="traffic control setup to be applied")
    parser_cmd.add_argument("-v", "--verbose", action='store_true', required=False, default=False,
                            help="more verbose output (default: %(default)s)")
    parser_cmd.add_argument("-i", "--interface", required=False, default='lo',
                            help="the network device name (default: %(default)s)")
    parser_cmd.add_argument("-c", "--clear", action='store_true', required=False, default=False,
                            help="issue a chain clearing clause before the actual recipe (default: %(default)s)")
    parser_cmd.add_argument("-b", "--ifbdevice", nargs='?', const='setup', default=None,
                            help="for download (ingress) control, specifies which ifb device to use."
                                 " If not present, a new device will be set up and used. (default: %(default)s)")
    parser_cmd.add_argument("-u", "--upload", default=None, nargs='+', type=str,
                            metavar='PROTOCOL:PORTTYPE:RANGE:RATE:JITTER',
                            help="define discipline classes for upload (egress) port range. Example:"
                                 " tcp:dport:16000-24000:512kbit:5%%. PROTOCOL, PORTTYPE and RANGE are required."
                                 " RATE and/or JITTER must be present. PROTOCOL is one of 'tcp', 'udp'."
                                 " PORTTYPE is one of 'sport', 'dport'. RANGE is a dash-delimited range of ports"
                                 " MINPORT-MAXPORT (inclusive), a single port or the keyword 'all'.")
    parser_cmd.add_argument("-d", "--download", default=None, nargs='+', type=str,
                            metavar='PROTOCOL:PORTTYPE:RANGE:RATE:JITTER',
                            help="define discipline class(es) for download (ingress) port range(s). Example:"
                                 " tcp:dport:16000-24000:512kbit:5%%. PROTOCOL, PORTTYPE and RANGE are required."
                                 " RATE and/or JITTER must be present. PROTOCOL is one of 'tcp', 'udp'."
                                 " PORTTYPE is one of 'sport', 'dport'. RANGE is a dash-delimited range of ports"
                                 " MINPORT-MAXPORT (inclusive), a single port or the keyword 'all'.")

    args = parser.parse_args(argv)
    args.verbose = args.verbose or old_args_dict.get('verbose', False)

    if not args.subparser:
        parser.error('No action requested.')

    if args.subparser == 'tc':
        args.clearonly_mode = args.clear and not (args.upload or args.download)
        if args.clearonly_mode:
            # artificially made to be "not False":
            args.upload = [':dummy:']
            args.download = [':dummy:']

        if not (args.upload or args.download or args.clear):
            parser.error('No action requested: add at least one of --upload, --download, --clear.')

        if not args.ifbdevice and (args.download or args.clearonly_mode):
            args.ifbdevice = 'setup'
        args.ifbdevice = determine_ifb_device(args.ifbdevice, args.verbose, parser)
    else:
        args.ifbdevice = None
    return args


def build_basics(target, tcp_all_rate, udp_all_rate):
    root_qdisc = target.set_root_qdisc('htb')

    tcp_rate = tcp_all_rate if tcp_all_rate else '15gbit'
    udp_rate = udp_all_rate if udp_all_rate else '15gbit'
    tcp_class = target.add_class('htb', root_qdisc, rate=tcp_rate)
    udp_class = target.add_class('htb', root_qdisc, rate=udp_rate)

    tcp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 6 0xff", flownode=tcp_class)
    udp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 17 0xff", flownode=udp_class)

    tcp_qdisc = target.add_qdisc('htb', tcp_class)
    udp_qdisc = target.add_qdisc('htb', udp_class)

    return tcp_qdisc, udp_qdisc


def build_single_port_filter(target, parent, flownode, port, port_dir):
    target.add_filter('u32', parent, 'ip {} {} 0xffff'.format(port_dir, port), flownode)


def parse_branch_list(args_list):
    branches = list()
    for args_str in args_list:
        current = parse_branch(args_str)
        branches.append(current)
    return branches


def build_tree(target, tcphook, udphook, args_list):
    branches = parse_branch_list(args_list)
    for branch in branches:
        if branch['range'] == 'all':
            continue

        if branch['porttype'] == 'sport':
            offset = 0
        elif branch['porttype'] == 'dport':
            offset = 2
        else:
            raise RuntimeError('UNREACHABLE!')

        if branch['protocol'] == 'tcp':
            hook = tcphook
        elif branch['protocol'] == 'udp':
            hook = udphook
        else:
            raise RuntimeError('UNREACHABLE')

        # class(htb) - shaping
        rate = branch['rate'] if branch['rate'] else '15gbit'  # TODO: move this to a constant
        htb_class = target.add_class('htb', hook, rate=rate)
        # filter(basic) - port
        if '-' not in branch['range']:
            build_single_port_filter(target, hook, htb_class, branch['range'], branch['porttype'])
        else:
            start, end = (int(elm) for elm in branch['range'].split("-"))
            cond_port_range = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
                .format(offset, start - 1, offset, end + 1)
            basic_filter = target.add_filter('basic', hook, cond=cond_port_range, flownode=htb_class)
        # qdisc(netem) - loss
        if branch['loss']:
            netem_qdisc = target.add_qdisc('netem', parent=htb_class, loss=branch['loss'], limit=NETEM_LIMIT)


def determine_all_rates(upload, download):
    tcp_all_rate = False  # serves as flag too
    udp_all_rate = False  # serves as flag too
    for groups in (upload, download):
        if not groups:
            continue
        for group in groups:
            parsed = parse_branch(group)
            if parsed['range'] == 'all' and parsed['protocol'] == 'tcp':
                if tcp_all_rate:
                    raise ParserError("More than one 'all' range detected for the same protocol(tcp).")
                tcp_all_rate = parsed['rate']
            elif parsed['range'] == 'all' and parsed['protocol'] == 'udp':
                if udp_all_rate:
                    raise ParserError("More than one 'all' range detected for the same protocol(udp).")
                udp_all_rate = parsed['rate']
    return tcp_all_rate, udp_all_rate


class SimpleNamespace(object):
    def __repr__(self):
        return "<SimpleNamespace({!r}) at 0x{:016x}>".format(self.__dict__, id(self))


class SimNetPlugin(object):

    def __init__(self, args=None, target_factory=None):
        """Initializer.
        :param args: parser.Namespace - the command line argumets
        :param target_factory: callable returning ITarget - the target factory
               to create the target chanin builders with
        """
        self._target_factory = target_factory

        if args is None:
            self._args = SimpleNamespace()

            # the default values must match the argparse defaults for these arguments
            self.configure(clear=False, verbose=False, interface='lo', ifbdevice=None)
            self._args.upload = list()
            self._args.download = list()

            #: intrenal helper flag which indicates input that requres clearing the chain(s) but no qdisc setup
            self._args.clearonly_mode = False

        else:
            self._args = args

    def configure(self, clear='<undef>', verbose='<undef>', interface='<undef>', ifbdevice='<undef>'):
        """Configures the general options given as named arguments.

        :param clear: bool - whether to generate a clearing command at the command sequence start
        :param verbose: bool - whether to be verbose
        :param interface: string - the network device name
        :param ifbdevice: string - the ifb network device name, if any
        """
        self._args.clear = clear if clear != '<undef>' else self._args.clear
        self._args.verbose = verbose if verbose != '<undef>' else self._args.verbose
        self._args.interface = interface if interface != '<undef>' else self._args.interface
        self._args.ifbdevice = ifbdevice if ifbdevice != '<undef>' else self._args.ifbdevice

    def setup(self, upload=None, download=None, protocol=None, porttype=None, range=None,
              rate=None, jitter=None):
        """Sets up traffic control disciplines effectively limiting the traffic for given direction,
        protocol, port types, port ranges with given rate and introducing an optional jitter.
        Note that only one of ``uplaod`` or ``download`` can be set. For configuring disciplines
        for both directions, repeat this ``setup()`` call with the alternative arguments.

        :param upload: bool - indicated upload direction (ingress)
        :param download: bool - indicated download direction (egress)
        :param protocol: string - the Internet protocol, currently one of 'tcp' or 'udp'
        :param porttype: string - the port type, one of 'sport' -- indicated source port control,
                                   or 'dport' -- indicates destination port control
        :param range: string - the port or port range boundaries, dash-delimited (e.g. '8080' or '8000-8088')
        :param rate: string - the rate limit as understood by ``/sbin/tc`` sub-commands (pleae refer to
                               ``tc`` man pahe)
        :param jitter: string - the packet loss percent, acompanied by the percent sign, e.g. '7%'
        """
        assert bool(upload) != bool(download), \
            "exactly one of `upload`, `download` must be True, got upload={!r}, download={!r}".format(upload, download)

        seq = (elm for elm in (protocol, porttype, range, rate, jitter) if elm is not None)
        token = ":".join(seq)
        thelist = self._args.upload if upload else self._args.download
        thelist.append(token)

    def marshal(self):
        """Applies setup recipe instruction already built."""
        # Note that TrafficControl.get_interface() returns a "Null" NetDevice object if device name is None
        #print(self._args)
        iface = NetDevice.get_interface(self._args.interface, self._target_factory)
        ifbdev = NetDevice.get_interface(self._args.ifbdevice, self._target_factory)

        if self._args.upload:
            if self._args.clear:
                iface.egress.clear()
            if not self._args.clearonly_mode:
                tcp_all_rate, udp_all_rate = determine_all_rates(self._args.upload, self._args.download)
                tcp_hook, udp_hook = build_basics(iface.egress, tcp_all_rate, udp_all_rate)
                build_tree(iface.egress, tcp_hook, udp_hook, self._args.upload)

            iface.egress.configure(verbose=self._args.verbose)
            iface.egress.marshal()

        if self._args.download:
            if self._args.clear:
                iface.ingress.clear()
                ifbdev.egress.clear()
            if not self._args.clearonly_mode:
                iface.ingress.set_redirect(iface, ifbdev)
                tcp_all_rate, udp_all_rate = determine_all_rates(self._args.upload, self._args.download)
                tcp_hook, udp_hook = build_basics(ifbdev.egress, tcp_all_rate, udp_all_rate)
                build_tree(ifbdev.egress, tcp_hook, udp_hook, self._args.download)

            iface.ingress.configure(verbose=self._args.verbose)
            iface.ingress.marshal()
            ifbdev.egress.configure(verbose=self._args.verbose)
            ifbdev.egress.marshal()

    def load_profile(self, profile_name, config_file=None):
        profile_args = parse_ini_file(profile_name, config_file, self._args.verbose)
        old_args_dict = self._args.__dict__.copy()
        self._args = parse_args(profile_args, old_args_dict)


def plugin_main(argv, target_factory):
    if not argv:
        argv = sys.argv[1:]
    handle_version_arg(argv)
    args = parse_args(argv)
    if args.verbose:
        print("Args:", str(args).lstrip("Namespace"))

    simnet = SimNetPlugin(args, target_factory)
    if 'profile_name' in args:
        simnet.load_profile(args.profile_name, args.config)
        # profile_args = parse_ini_file(args.profile_name, args.config, args.verbose)
        # old_args_dict = args.__dict__.copy()
        # args = parse_args(profile_args, old_args_dict)

    #simnet = SimNetPlugin(args, target_factory)
    simnet.marshal()
