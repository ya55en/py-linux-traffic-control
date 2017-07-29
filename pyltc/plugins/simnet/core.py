"""
Chad Phillips' (thehunmonkgroup @ github) network simulation plugin.

``simnet`` allows for simulating network conditions related to bandwidth
limitations (done via htb-based traffic shapping) as well as packet loss
(achieved using the netem qdisc loss simulation).

"""

from pyltc.core.netdevice import DeviceManager, NetDevice
from pyltc.util.misc import SimpleNamespace, Undef
from pyltc.util.argsparse import ArgParseError
from pyltc.plugins.simnet.util import BranchParser
from pyltc.core.plug import PyltcPlugin


#: netem (the qdisc that simulates special network conditions) works for a
#: default of 1000 packets. This was a source of problems and the workaround
#: currently is to set it to a very large number. Beware that if you keep
#: that filter on for too long, this limit may be reached.
NETEM_LIMIT = 1000000000


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


def parse_branch_list(args_list, upload, download):
    branches = list()
    for args_str in args_list:
        current = BranchParser(args_str, upload=upload, download=download).as_dict()
        branches.append(current)
    return branches


def build_tree(target, tcphook, udphook, args_list, upload=None, download=None):
    branches = parse_branch_list(args_list, upload=upload, download=download)
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

        # traffic shaping via class htb
        rate = branch['rate'] if branch['rate'] else '15gbit'  # TODO: move this to a constant
        htb_class = target.add_class('htb', hook, rate=rate)

        # basic filter for port range
        if '-' not in branch['range']:
            build_single_port_filter(target, hook, htb_class, branch['range'], branch['porttype'])
        else:
            start, end = (int(elm) for elm in branch['range'].split("-"))
            cond_port_range = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
                .format(offset, start - 1, offset, end + 1)
            basic_filter = target.add_filter('basic', hook, cond=cond_port_range, flownode=htb_class)

        # loss simulation via netem qdisc
        if branch['loss']:
            netem_qdisc = target.add_qdisc('netem', parent=htb_class, loss=branch['loss'], limit=NETEM_LIMIT)


def determine_all_rates(upload, download):
    tcp_all_rate = False  # serves as flag too
    udp_all_rate = False  # serves as flag too
    for groups in (upload, download):
        if not groups:
            continue
        for group in groups:
            # parsed = parse_branch(group)
            parsed = BranchParser(group, dontcare=True).as_dict()  # in this case we don't care for direction
            if parsed['range'] == 'all' and parsed['protocol'] == 'tcp':
                if tcp_all_rate:
                    raise ArgParseError("More than one 'all' range detected for the same protocol (tcp).")
                tcp_all_rate = parsed['rate']

            elif parsed['range'] == 'all' and parsed['protocol'] == 'udp':
                if udp_all_rate:
                    raise ArgParseError("More than one 'all' range detected for the same protocol (udp).")
                udp_all_rate = parsed['rate']
    return tcp_all_rate, udp_all_rate


class SimNetPlugin(PyltcPlugin):

    __plugin_name__ = 'simnet'

    @classmethod
    def add_subparser(cls, subparsers):
        subparser = subparsers.add_parser(cls.__plugin_name__,
                                          help="network simulation (simnet) traffic control setup")

        subparser.add_argument('-v', '--verbose', action='store_true', required=False, default=False,
                               help="more verbose output (default: %(default)s)")

        subparser.add_argument('-i', '--interface', required=False, default='lo',
                               help="the network device name (default: %(default)s)")

        subparser.add_argument('-c', '--clear', action='store_true', required=False, default=False,
                               help="issue a chain clearing clause before the actual recipe (default: %(default)s)")

        subparser.add_argument('-b', '--ifbdevice', nargs='?', const='ifb', default=None,
                               help="for download (ingress) control, specifies which ifb device to use."
                                     " If not present, a new device will be set up and used. (default: %(default)s)")

        subparser.add_argument('-u', '--upload', default=None, nargs='*', type=str,
                               metavar='PROTOCOL:PORTTYPE:RANGE:RATE:JITTER',
                               help="define discipline classes for upload (egress) port range. Example:"
                                    " tcp:dport:16000-24000:512kbit:5%%. PROTOCOL, PORTTYPE and RANGE are required."
                                    " RATE and/or JITTER must be present. PROTOCOL is one of 'tcp', 'udp'."
                                    " PORTTYPE is one of 'sport', 'dport', 'lport', 'rport'."
                                    " RANGE is a dash-delimited range of ports MINPORT-MAXPORT (inclusive),"
                                    " a single port or the keyword 'all'.")

        subparser.add_argument('-d', '--download', default=None, nargs='*', type=str,
                               metavar='PROTOCOL:PORTTYPE:RANGE:RATE:JITTER',
                               help="define discipline class(es) for download (ingress) port range(s). Example:"
                                    " tcp:dport:16000-24000:512kbit:5%%. PROTOCOL, PORTTYPE and RANGE are required"
                                    " and have the same values as for '--upload' above.")

        # @classmethod
        # def get_meta(cls):
        #     meta = {
        #         'help_description': "network simulation (simnet) traffic control setup",
        #     }
        #     return meta

    @classmethod
    def post_parse_process(cls, args):
        if not (args.upload or args.download or args.clear):
            raise ArgParseError("no action requested: add at least one of --upload, --download, --clear.")

        if not DeviceManager.device_exists(args.interface):
            raise ArgParseError("device NOT found: {!s}".format(args.interface))

        if args.clear and args.upload is None and args.download is None:
            args.upload = list()
            args.download = list()

    def __init__(self, args=None, target_factory=None):
        """Initializer.
        :param args: parser.Namespace - the command line argumets
        :param target_factory: callable returning ITarget - the target factory
               to create the target chanin builders with
        """
        super().__init__(args=args, target_factory=target_factory)
        if args is None:
            self._args = SimpleNamespace()

            # the default values must match the argparse defaults for these arguments
            self.configure(clear=False, verbose=False, interface='lo', ifbdevice=None)
            self._args.upload = list()
            self._args.download = list()

            #: internal helper flag which indicates input that requires clearing the chain(s) but no qdisc setup
            self._args.clearonly_mode = False

    def configure(self, clear=Undef, verbose=Undef, interface=Undef, ifbdevice=Undef):
        """Configures the general options given as named arguments.

        :param clear: bool - whether to generate a clearing command at the command sequence start
        :param verbose: bool - whether to be verbose
        :param interface: string - the network device name
        :param ifbdevice: string - the ifb network device name, if any
        """
        self._args.clear = clear if clear is not Undef else self._args.clear
        self._args.verbose = verbose if verbose is not Undef else self._args.verbose
        self._args.interface = interface if interface is not Undef else self._args.interface
        self._args.ifbdevice = ifbdevice if ifbdevice is not Undef else self._args.ifbdevice

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
        # Note that NetDevice.get_device() returns a "Null" NetDevice object if device name is None
        #print(self._args)
        iface = NetDevice.get_device(self._args.interface, self._target_factory)

        # ifbdev = 'ifb' if self._args.download and not self._args.ifbdevice else None

        if (self._args.download is not None) and (not self._args.ifbdevice):
            self._args.ifbdevice = 'ifb'

        ifbdev = NetDevice.get_device(self._args.ifbdevice, self._target_factory)
        ifbdev.up()

        if self._args.upload is not None:

            if self._args.clear:
                iface.egress.clear()

            if self._args.upload:  # not self._args.clearonly_mode:
                tcp_all_rate, udp_all_rate = determine_all_rates(self._args.upload, self._args.download)
                tcp_hook, udp_hook = build_basics(iface.egress, tcp_all_rate, udp_all_rate)
                build_tree(iface.egress, tcp_hook, udp_hook, self._args.upload, upload=True)

            iface.egress.configure(verbose=self._args.verbose)
            iface.egress.marshal()

        if self._args.download is not None:

            if self._args.clear:
                iface.ingress.clear()
                ifbdev.egress.clear()

            if self._args.download: # not self._args.clearonly_mode:
                iface.ingress.set_redirect(iface, ifbdev)
                tcp_all_rate, udp_all_rate = determine_all_rates(self._args.upload, self._args.download)
                tcp_hook, udp_hook = build_basics(ifbdev.egress, tcp_all_rate, udp_all_rate)
                build_tree(ifbdev.egress, tcp_hook, udp_hook, self._args.download, download=True)

            iface.ingress.configure(verbose=self._args.verbose)
            iface.ingress.marshal()
            ifbdev.egress.configure(verbose=self._args.verbose)
            ifbdev.egress.marshal()
