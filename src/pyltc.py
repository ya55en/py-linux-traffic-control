#! /usr/bin/env python3
"""

pyltc.py

The py-linux-traffic-control tool (still alpha).

Coding convention follows pep8 (with some purposeful deviations), comments
formatting mostly follows pep257, line length is 112 characters, comments
wrapped at 80 characters.

:author: Yassen Damyanov <yd-at-itlabs.bg>

"""

import os
import io
from abc import abstractmethod, ABC
import subprocess
from subprocess import PIPE, TimeoutExpired


__version__ = (0, 1, 4)
__build__ = 29
__maintainer__ = "Yassen Damyanov <yd-at-itlabs.bg>"

#: netem (the qdisc that simulates special network conditions) works for a
# default of 1000 packets. This was a source of problems and the workaround
# that I came up with currently is to set it to a very large  number.
#: Chad: Beware that if you keep that filter on for too long, this limit may
# be reached.
NETEM_LIMIT = 1000000000

CONFIG_PATHS = (
    './pyltc.conf',
    '/etc/pyltc.conf',
)
DIR_EGRESS = 'egress'
DIR_INGRESS = 'ingress'


def popen_factory():
    """Returns subprocess.Popen on Linux, otherwise returns MockPopen
       class assuming this is a test run."""
    import platform
    if platform.system() == 'Linux':
        return subprocess.Popen

    class MockPopen(object):
        """Mocks command execution to allow testing on non-Linux OS."""
        def __init__(self, command_list, *args, **kw):
            self._cmd_list = command_list
            self._args = args
            self._kw = kw
            self.returncode = 0
        def communicate(self, timeout=None):
            if self._cmd_list[0].endswith('echo'):
                return bytes(" ".join(self._cmd_list[1:]), encoding='utf-8'), None
            if self._cmd_list[0].endswith('/bin/true'):
                return None, None
            if self._cmd_list[0].endswith('/bin/false'):
                self.returncode = 1
                return None, None
            if self._cmd_list[0].endswith('sleep'):
                import time
                pause = float(self._cmd_list[1])
                if timeout and timeout < pause:
                        time.sleep(timeout)
                        cmd = " ".join(self._cmd_list)
                        raise TimeoutExpired(cmd, timeout)
                time.sleep(pause)
                return None, None
            raise RuntimeError("UNREACHABLE")
    return MockPopen


class CommandFailed(Exception):

    def __init__(self, command):
        assert isinstance(command, CommandLine) and command.returncode, \
                 "expecting failed command, got {!r}".format(command)
        output = command.stderr
        if command.stdout:
            output = "out:{}\nerr: {}".format(command.stdout, output)
        msg = output if output.strip() else "Command failed: {!r}".format(command.cmdline)
        msg = msg.rstrip() + " (rc={})".format(command.returncode)
        super(CommandFailed, self).__init__(msg)
        self._command = command

    @property
    def returncode(self):
        return self._command.returncode


class CommandLine(object):
    """Command line execution class."""

    def __init__(self, cmdline, ignore_errors=False):
        self._cmdline = cmdline
        self._ignore_errors = ignore_errors
        self._returncode = None
        self._stdout = None
        self._stderr = None

    @property
    def cmdline(self):
        return self._cmdline

    def _construct_cmd_list(self, command):
        """Recursively process the command string to exctract any quoted segments
           as a single command element.
           """
        quote_count = command.count('"')
        if quote_count % 2 != 0:
            raise RuntimeError('Unbalanced quotes in command: {!r}'.format(command))
        if quote_count == 0:
            return command.split()
        left, mid, right = command.split('"', 2)
        return left.split() + [mid] + self._construct_cmd_list(right)

    def execute(self, timeout=10):
        """Prepares and executes the command."""
        command_list = self._construct_cmd_list(self._cmdline)
        PopenClass = popen_factory()
        proc = PopenClass(command_list, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate(timeout=timeout)
        self._stdout = stdout.decode('unicode_escape') if stdout else ""
        self._stderr = stderr.decode('unicode_escape') if stderr else ""
        rc = proc.returncode
        self._returncode = rc
        if rc and not self._ignore_errors:
            raise CommandFailed(self)
        return self  # allows one-line creation + execution with assignment

    @property
    def returncode(self):
        return self._returncode

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr


class LtcNode(ABC):
    """Superclass for nodes of the traffic control chain structure."""

    def __init__(self, name, parent, **kw):
        """Initializes this node.

        :param name: string - this node's name, e.g. 'htb'
        :param parent: LtcNode - the parent LtcNode object or None
        :param kw: dict - the keyword arguments for this object
        """
        self._name = name
        self._parent = parent
        self._params = kw
        self._major = None
        self._minor = None

    def cmd_repr(self):
        """Represents this node as a tc-compatible sub-command.
           :return: string - the tc-compatible sub-command, e.g.
                    'htb rate 256kbit'
        """
        if not self._params:
            return self._name
        sorted_seq = sorted(self._params.items(), key=lambda tpl: tpl[0])
        kwargs = " ".join(('{} {}'.format(key, value) for key, value in sorted_seq if value is not None))
        return '{} {}'.format(self._name, kwargs)

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @property
    def params(self):
        return self._params

    @property
    def nodeid(self):
        return "{}:{}".format(self._major, self._minor)


class Qdisc(LtcNode):
    """Represents a queuing discipline node in the LTC chain structure."""

    _major_counter = 1

    def __init__(self, name, parent, **kw):
        """Initializes this node.
           See LtcNode.__init__() docstring.
        """
        super(Qdisc, self).__init__(name, parent, **kw)
        self._major = self.__class__._major_counter
        self.__class__._major_counter += 1
        self._minor = 0
        self._class_minor = 0

    def new_class_id(self):
        """Creates and returns a new LTC classid as a (major, minor) tuple.
           The major is the same as the major of this qdisc object.
           :return: tuple - two-element tuple (major, minor)
        """
        self._class_minor += 1
        return (self._major, self._class_minor)

    @property
    def handle(self):
        """Returns the handle of this qdisc object.
           :return: string - the handle as string, e.g. '1:0'
        """
        return self.nodeid


class QdiscClass(LtcNode):
    """Represents a class node of a queuing discipline in the LTC chain
       structure."""

    def __init__(self, name, parent, **kw):
        super(QdiscClass, self).__init__(name, parent, **kw)
        self._major, self._minor = parent.new_class_id()
        self._name = name
        self._parent = parent
        self._params = kw

    @property
    def classid(self):
        """Returns the classid of this qdisc class object.
           :return: string - the classid as string, e.g. '1:1'
        """
        return self.nodeid


class Filter(object):
    """Represents a filter node in the LTC chain structure."""

    _handle_counter = 1

    def __init__(self, name, parent, cond, flownode, **kw):
        # TODO: implement proper data handling
        self._handle = self.__class__._handle_counter
        self.__class__._handle_counter += 1

    @property
    def nodeid(self):
        return self._handle


def default_target_factory(iface, direction):
    """
    The default target factory. If no custom factory is provided to the
    framework, this factory is used by the Interface.__init__() method to
    connfigure its egress and ingress target builders.

    A custom target factory may be provided to the Interface.__init__() that
    returns a target instance (that is, a class implementing ITarget).

    As the ITarget interface limits the arguments at creation time, the
    ITarget.configure() method can be used to further configure a target object.

    :param iface: Interface - the interface object :param direction: string - a
                  string representing flow direction (DIR_EGRESS or DIR_INGRESS)
    :return: ITarget - the ITarget object created by this factory.
    """
    accepted_values = (DIR_EGRESS, DIR_INGRESS)
    assert direction in accepted_values, "direction must be one of {!r}".format(accepted_values)
    filename = "{}-{}.tc".format(iface.name, direction)
    return TcCommandTarget(iface, filename)


class Interface(object):
    """
    Represents a network interface device with a name and an egress and ingress
    LTC chains.
    """

    def __init__(self, name, target_factory=default_target_factory):
        """
        Initializes this interface object. See default_target_factory for
        details about the target_factory argument.

        :param name: string - the name of the network device, e.g. 'eth0'
        :param target_factory: function - implements the default_target_factory
                               signature.
        """
        self._name = name
        self._egress_chain = target_factory(self, DIR_EGRESS)
        self._ingress_chain = target_factory(self, DIR_INGRESS)

    @property
    def name(self):
        """Returns the name of this interface."""
        return self._name

    @property
    def ingress(self):
        """Returns the ingress chain builder for this interface.
           :return: ITarget - the ingress chain target builder
        """
        return self._ingress_chain

    @property
    def egress(self):
        """Returns the egress chain builder for this interface.
           :return: ITarget - the egress chain target builder
        """
        return self._egress_chain

    def install(self, direction, *args, **kw):
        """
        Installs the chains for this interface. If direction is None, installs
        both chains egress and ingres, in this order.

        :param direction: - string - the direction chain (DIR_EGRESS or
                            DIR_INGRESS)
        """
        accepted_values = (DIR_EGRESS, DIR_INGRESS)
        assert direction in accepted_values, "direction must be one of {!r}".format(accepted_values)
        if direction is None:
            self._egress_chain.install(*args, **kw)
            self._ingress_chain.install(*args, **kw)
            return
        if direction == DIR_EGRESS:
            self._egress_chain.install(*args, **kw)
            return
        if direction == DIR_INGRESS:
            self._ingress_chain.install(*args, **kw)
            return
        raise RuntimeError("UNREACHABLE!")


class ITarget(ABC):
    """Represents an installation method of the LTC configuration."""

    @abstractmethod
    def __init__(self, iface, direction=DIR_EGRESS):
        """
        Initializes this target object.

        :param iface: Interface - the interface object
        :param direction: string - a string representing flow direction
                          (DIR_EGRESS or DIR_INGRESS)
        """

    @abstractmethod
    def configure(self, *args, **kw):
        """Configures this target after creation."""

    @abstractmethod
    def clear(self):
        """Builds an recipe for clearing the LTC chain."""

    @abstractmethod
    def set_root_qdisc(self, name, **kw):
        """
        Builds a recipe step for setting the root qdisc of the LTC chain and
        returns a Qdisc object with appropriate handle for further reference.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param kw: dict - any arguments passed to the qdisc
        :return: Qdisc - a newly created Qdisc object with a proper handler
        """

    @abstractmethod
    def add_qdisc(self, name, parent, **kw):
        """
        Builds a recipe step for adding a qdisc to the LTC chain and returns
        a Qdisc object with appropriate handle for further reference.
        If parent is None, builds an recipe for setting up the root qdisc.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param parent: QdiscClass - a qdisc class object to set this qdisc at
        :param kw: dict - any arguments passed to the qdisc
        :return: Qdisc - a newly created Qdisc object with a proper handler
        """

    @abstractmethod
    def add_class(self, name, parent, **kw):
        """
        Builds an recipe for adding a qdisc class to the LTC chain and returns
        a QdiscClass object with appropriate handle for further reference.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param parent: QdiscClass - a qdisc class object to set this qdisc at
        :param kw: dict - any arguments passed to the qdisc
        """

    @abstractmethod
    def add_filter(self, name, parent, cond, flownode):
        """
        Builds an recipe for adding a qdisc class to the LTC chain and returns
        a QdiscClass object with appropriate handle for further reference.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param parent: QdiscClass - a qdisc class object to set this qdisc at
        :param kw: dict - any arguments passed to the qdisc
        """

    @abstractmethod
    def install(self):
        """
        Installs the actions already built within this target object.
        Examples for "installing": create a file with tc commands, or
        live execution of the tc commands to actually configure the kernel.
        """


class TcFileTarget(ITarget):
    """
    An ITarget (see ITarget docstrings) implementation that builds /sbin/tc
    compatible commands and finally represents them as a multi-line string or
    saves them into a file.
    """

    def __init__(self, iface, direction=DIR_EGRESS):
        """
        Initializes this target object.
        :param iface: Interface - the interface this target is associated with
        :param direction: string - a string representing flow direction
                          (DIR_EGRESS or DIR_INGRESS)
        """
        self._iface = iface
        self._filename = "{}-{}.tc".format(iface.name, direction)
        self._commands = list()

    def clear(self):
        cmd = "tc qdisc del dev {} root".format(self._iface.name)
        self._commands.append(cmd)

    def configure(self, filename):
        self._filename = filename

    def set_root_qdisc(self, name, **kw):
        return self.add_qdisc(name, None, **kw)

    def add_qdisc(self, name, parent, **kw):
        qdisc = Qdisc(name, parent, **kw)
        cmd_params = {
            'iface': self._iface.name,
            'parent': 'parent ' + parent.classid if parent else 'root',
            'handle': qdisc.handle,
            'qdisc_repr': qdisc.cmd_repr(),
        }
        cmd = "tc qdisc add dev {iface} {parent} handle {handle} {qdisc_repr}".format(**cmd_params)
        self._commands.append(cmd)
        return qdisc

    def add_class(self, name, parent, **kw):
        klass = QdiscClass(name, parent, **kw)
        cmd_params = {
            'iface': self._iface.name,
            'parentid': parent.handle,
            'classid': klass.classid,
            'klass_repr': klass.cmd_repr(),
        }
        cmd = "tc class add dev {iface} parent {parentid} classid {classid} {klass_repr}".format(**cmd_params)
        self._commands.append(cmd)
        return klass

    def add_filter(self, name, parent, cond, flownode, **kw):
        filter = Filter(name, parent, cond, flownode, **kw) # TODO: filter to accept or generate prio and handle
        cmd_params = {
            'name': name,
            'iface': self._iface.name,
            'parentid': parent.nodeid,
            'cond': cond,
            'flowid': flownode.nodeid,
#             'handle': filter._handle,
        }
        cmd = ("tc filter add dev {iface} parent {parentid} protocol ip prio 1"
               " {name} match {cond} flowid {flowid}").format(**cmd_params)
        self._commands.append(cmd)
        return filter

    def install(self, verbose=False):
        result = '\n'.join(self._commands)
        if verbose:
            print(result)
        with open(self._filename, 'w') as fhl:
            fhl.write(result + '\n')


class TcCommandTarget(TcFileTarget):
    """
    An ITarget (see ITarget docstrings) implementation that builds /sbin/tc
    compatible commands and executes them.
    """
    def __init__(self, iface, direction=DIR_EGRESS):
        super(TcCommandTarget, self).__init__(iface, direction=direction)

    def install(self, verbose=False):
        try:
            self._install(verbose=verbose)
        except CommandFailed as exc:
            print(exc)

    def _install(self, verbose=False):
        for idx, cmd_str in enumerate(self._commands):
            should_ignore_errs = (idx == 0 and " del" in cmd_str)
            if verbose:
                print("--> {!r}".format(cmd_str))
            cmd = CommandLine(cmd_str, ignore_errors=should_ignore_errs).execute()
            #if verbose:
            #    print("code: {}, out: {}, err: {}".format(cmd.returncode, cmd.stdout, cmd.stderr))
        #return super(TcCommandTarget, self).install(verbose=True)


class TrafficControl(object):
    """A facade for convenient use of the pyltc framework."""

    _iface_map = None

    @classmethod
    def init(cls):
        cls._iface_map = dict()
        Qdisc._major_counter = 1

    @classmethod
    def get_iface(cls, ifname):
        try:
            return cls._iface_map[ifname]
        except KeyError:
            iface = Interface(ifname)
            cls._iface_map[ifname] = iface
            return iface


class IllegalState(Exception):
    pass

class MisconfigurationError(Exception):
    pass


class ConfigParser(object):

    def __init__(self, input=None):
        self._sections = None
        self._filename = None
        self._stream = None
        if input is None:
            return
        if isinstance(input, str):
            self._filename = input
        elif hasattr(input, 'write'):
            self._stream = input
        else:
            raise TypeError("Expecting filename (str) or file object, got %s", type(input))

    def _ensure_stream_open(self):
        if self._filename:
            return open(self._filename)
        if self._stream:
            return self._stream
        raise IllegalState("Povide filename or stream")

    def parse(self):
        with self._ensure_stream_open() as fhl:
            content = fhl.read()
        content = "\n" + content
        raw_sections = [section for section in content.split("\n[") if section]
        raw_sections = [elm.replace("\n", " --") for elm in raw_sections]
        sections = dict()
        for section in raw_sections:
            rec = [elm for elm in section.split() if elm != '--']
            sections[rec[0].rstrip("]")] = rec[1:]
        self._sections = sections
        return self

    def section(self, name):
        if not self._sections:
            raise IllegalState("Call parse() first")
        return self._sections[name]

def shape_ports(target, direction, range, rate, loss=None):
    """
    The only recipe that we support currently. Creates a LTC (egress) chain
    that shapes the traffic for a range of tcp ports into a given rate using
    htb. If loss is provided, adds simulated jitter using netem.
    """
    rootqd = target.set_root_qdisc('htb')
    htbclass = target.add_class('htb', parent=rootqd, rate=rate)
    if loss:
        target.add_qdisc('netem', parent=htbclass, loss=loss, limit=NETEM_LIMIT) # e.g. 'loss random 7%'
    assert range.count("-") == 1, "illegal range: {!r}".format(range)   # we do not yet support complex ranges
    start, end = (int(elm) for elm in range.split("-"))
    accepted_values = ('dport', 'sport')
    assert direction in accepted_values, \
            "direction ({!r}) must be one of {!r}".format(direction, accepted_values)
    offset = 0 if direction == 'sport' else 2
    cond = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
            .format(offset, start - 1, offset, end + 1)
    target.add_filter('basic', rootqd, cond=cond, flownode=htbclass)


def threefold(target, range, rate, loss=None):
    """HTB-based hirarchical system."""
    rootqd = target.set_root_qdisc('htb', default=1)
    default_class = target.add_class('htb', parent=rootqd)
    default_qdisc = target.add_qdisc('pfifo', parent=default_class, limit=4096)
    shaped_class = target.add_class('htb', parent=rootqd, rate=rate)
    assert range.count("-") == 1, "illegal range: {!r}".format(range)   # we do not yet support complex ranges
    start, end = (int(elm) for elm in range.split("-"))
    offset = 2 # dpoort
    cond = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
            .format(offset, start - 1, offset, end + 1)
    target.add_filter('basic', rootqd, cond=cond, flownode=shaped_class)


def shape_dports(chain, range, rate, loss=None):
    return chain.shape_ports('dport', range, rate, loss)

def shape_sports(chain, range, rate, loss=None):
    return chain.shape_ports('sport', range, rate, loss)


def build_basics(target):
    root_qdisc = target.set_root_qdisc('htb')
    tcp_class = target.add_class('htb', root_qdisc, rate='30gbit')
    udp_class = target.add_class('htb', root_qdisc, rate='30gbit')

    tcp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 6 0xff", flownode=tcp_class)
    udp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 17 0xff", flownode=udp_class)

    tcp_qdisc = target.add_qdisc('htb', tcp_class)
    udp_qdisc = target.add_qdisc('htb', udp_class)

    return tcp_qdisc, udp_qdisc

def parse_branch_list(args_list):
    branches = list()
    for args_str in args_list:
        current = {'protocol': None, 'range': None, 'rate': None, 'loss': None}
        branches.append(current)
        for part in args_str.split(':'):
            if '-' in part:
                current['range'] = part
            elif part.endswith('bit') or part.endswith('bps'):
                current['rate'] = part
            elif part.endswith('%'):
                current['loss'] = part
            elif part in ('tcp', 'udp'):
                current['protocol'] = part
            else: # unrecognizable protocol or nothing will be treated as tcp
                current['protocol'] = 'tcp'
    return branches

def build_tree(target, tcphook, udphook, args_list, offset):
    branches = parse_branch_list(args_list)
    for branch in branches:
        if branch['protocol'] == 'tcp':
            protocol_number = 6
            hook = tcphook
        elif branch['protocol'] == 'udp':
            protocol_number = 17
            hook = udphook
        else:
            raise MisconfigurationError("protocol not specified (tcp or udp?)")
            #raise RuntimeError('UNREACHABLE')

        # class(htb) - shaping
        rate = branch['rate'] if branch['rate'] else '30gbit'
        htb_class = target.add_class('htb', hook, rate=rate)
        # filter(basic) - port
        start, end = (int(elm) for elm in branch['range'].split("-"))
        cond_port = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"'.format(offset, start - 1, offset, end + 1)
        basic_filter = target.add_filter('basic', hook, cond=cond_port, flownode=htb_class)
        # qdisc(netem) - loss
        if branch['loss']:
            netem_qdisc = target.add_qdisc('netem', parent=htb_class, loss=branch['loss'], limit=NETEM_LIMIT)


ITarget.shape_ports = shape_ports
ITarget.shape_dports = shape_dports
ITarget.shape_sports = shape_sports


def determine_ini_conf_file():
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return os.path.abspath(path)

def parse_ini_file(profile, conf_file, verbose):
    if not conf_file:
        conf_file = determine_ini_conf_file()
    if not conf_file:
        return ['no_conf_file']
    if verbose:
        print('Using config file {!r}'.format(conf_file))

    conf_parser = ConfigParser(conf_file)
    conf_parser.parse()
    try:
        new_args = conf_parser.section(profile)
    except KeyError:
        return ['no_such_profile', '{!r}'.format(profile)]

    new_args.insert(0, 'tc')
    print(new_args)
    return new_args

#     with open(conf_file, 'r') as ini_file:
#         content = ini_file.read()
#     content = content.replace('%', '%%')
#
#     new_args = ['tc'] # TODO: Make it a constant.
#     ini_parser = configparser.ConfigParser(allow_no_value=True)
#     ini_parser.read_string(content)
#     if not profile in ini_parser.sections():
#         return ['no_such_profile']
#     for key in ini_parser[profile]:
#         new_args.append("--{}".format(key))
#         if ini_parser[profile][key]:
#             new_args.append(ini_parser[profile][key])
#     return new_args

def parse_args(argv):
    import argparse
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
                        help="generate a chain clearing clause before the actual recipe (default: %(default)s)")
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
    if args.subparser == 'tc' and not (args.sclass or args.dclass or args.clear):
        parser.error('No action requested: add at least one of --sclass, --dclass, --clear.')
    return args

def compose_version():
    name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
    version_str = ".".join(map(str, __version__))
    maintainer = __maintainer__.replace("-at-", "@")
    return "{} verison {} (maintaner: {})".format(name, version_str, maintainer)

def main(argv):
    if '-V' in argv or '--version' in argv:
        print(compose_version())
        sys.exit(0)
    args = parse_args(argv)
    #print(args)
    if args.subparser == 'version':
        name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
        print(name, "verison", ".".join(map(str, __version__)))
        sys.exit(0)
    if 'profile_name' in args:
        profile_args = parse_ini_file(args.profile_name, args.config, args.verbose)
        #print(profile_args)
        args = parse_args(profile_args)

    TrafficControl.init()
    iface = TrafficControl.get_iface(args.iface)
    if args.clear:
        iface.egress.clear()
    if args.dclass or args.sclass:
        tcp_hook, udp_hook = build_basics(iface.egress)
    if args.dclass:
        build_tree(iface.egress, tcp_hook, udp_hook, args.dclass, offset=2)
    if args.sclass:
        build_tree(iface.egress, tcp_hook, udp_hook, args.sclass, offset=0)
    iface.egress.install(verbose=args.verbose)


# ---- Test Section ---------------------------------------------------------


import unittest


class TestCmdFailedException(unittest.TestCase):

    def test_creation_default(self):
        self.assertRaises(TypeError, CommandFailed)

    def test_creation_w_command(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        exc = CommandFailed(cmd)
        self.assertEqual("Command failed: '/bin/false' (rc=1)", str(exc))

    def test_creation_w_non_command_fails(self):
        self.assertRaises(AssertionError, CommandFailed, "STRING")

    def test_returncode(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        exc = CommandFailed(cmd)
        self.assertEqual(cmd.returncode, exc.returncode)
        self.assertIsNotNone(exc.returncode)


class TestCommandLine(unittest.TestCase):

    def test_creation_default(self):
        self.assertRaises(TypeError, CommandLine)

    def test_creation_cmd_line(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual("/bin/true", cmd.cmdline)
        self.assertFalse(cmd._ignore_errors)

    def test_creation_cmd_line_ignore_errors(self):
        cmd = CommandLine("/bin/true", ignore_errors=True)
        self.assertEqual("/bin/true", cmd.cmdline)
        self.assertTrue(cmd._ignore_errors)

    def test_execute_simple(self):
        cmd = CommandLine("/bin/true")
        obj = cmd.execute()
        self.assertEqual(0, cmd.returncode)
        self.assertIs(cmd, obj)
        self.assertEqual("", cmd.stdout)
        self.assertEqual("", cmd.stderr)

    def test_execute_complex_success(self):
        cmd = CommandLine("echo ALPHA55 BRAVO55").execute()
        self.assertEqual(0, cmd.returncode)
        self.assertEqual("ALPHA55 BRAVO55", cmd.stdout.rstrip())
        self.assertEqual("", cmd.stderr)

    def test_ignore_error_false(self):
        cmd = CommandLine("/bin/false", ignore_errors=False)
        self.assertRaises(CommandFailed, cmd.execute)
        cmd = CommandLine("/bin/false")
        self.assertRaises(CommandFailed, cmd.execute)

    def test_ignore_error_true(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        self.assertNotEqual(0, cmd.returncode)
        self.assertIsNotNone(cmd.returncode)

    def test_timeout(self):
        cmd = CommandLine("/bin/sleep 1", ignore_errors=True)
        self.assertRaises(TimeoutExpired, cmd.execute, timeout=0.2)

    def test_wishful_api(self):
        cmd = CommandLine("echo ALPHA BRAVO").execute()
        self.assertEqual(0, cmd.returncode)
        self.assertEqual("ALPHA BRAVO", cmd.stdout.rstrip())
        self.assertEqual("", cmd.stderr)

        cmd = CommandLine("/bin/false", ignore_errors=False)
        self.assertRaises(Exception, cmd.execute)

        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        self.assertNotEqual(0, cmd.returncode)

    def test_construct_cmd_list_case_1(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual(['one', 'two', 'three'], cmd._construct_cmd_list('one two three'))

    def test_construct_cmd_list_case_2(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual(['one', 'two three', 'four'], cmd._construct_cmd_list('one "two three" four'))

    def test_construct_cmd_list_case_3(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual(['one', 'two three', 'four', 'five', 'asdasd quwey', 'qwe'], cmd._construct_cmd_list('one "two three" four five "asdasd quwey" "qwe"'))

    def test_construct_cmd_list_case_4(self):
        cmd = CommandLine("/bin/true")
        self.assertRaises(RuntimeError, cmd._construct_cmd_list, 'asd " asd"123"')

    def test_real(self):
        # FIXME: revisit this
        iface = Interface('veth15')
        target = TcCommandTarget(iface)
        target._commands = ['echo TEST_TEST', '/bin/true', 'echo (._. )']
        #target.install(verbosity=True)
        target.install(verbose=False)

class TestQdisc(unittest.TestCase):

    def test_creation(self):
        Qdisc._major_counter = 1
        qd1 = Qdisc('htb', None, rate='256kbit')
        self.assertEqual('1:0', qd1.handle)
        qd2 = Qdisc('htb', None, rate='512kbit')
        self.assertEqual('2:0', qd2.handle)

    def test_parent(self):
        parent_qdisc = Qdisc('htb', None, rate='256kbit')
        parent_class = QdiscClass('htb', parent_qdisc, rate='768kbit')
        qdisc = Qdisc('htb', parent_class, rate='256kbit')
        self.assertIs(parent_class, qdisc.parent)

    def test_kw(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil='512kbit')
        self.assertEqual('htb', qd.name)
        self.assertEqual({'rate': '256kbit', 'ceil': '512kbit'}, qd.params)

    def test_cmd_repr(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil='512kbit')
        self.assertEqual('htb ceil 512kbit rate 256kbit', qd.cmd_repr())

    def test_cmd_repr_no_args(self):
        qd = Qdisc('htb', None)
        self.assertEqual('htb', qd.cmd_repr())

    def test_cmd_repr_arg_is_none(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil=None)
        self.assertEqual('htb rate 256kbit', qd.cmd_repr())


class TestQdiscClass(unittest.TestCase):

    def test_creation(self):
        Qdisc._major_counter = 1
        parentqd = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parentqd, rate='768kbit')
        self.assertEqual('1:1', class1.classid)

    def test_parent(self):
        parent_qdisc = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parent_qdisc, rate='768kbit')
        self.assertIs(parent_qdisc, class1.parent)

    def test_kw(self):
        parentqd = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parentqd, rate='768kbit', ceil='1mbit')
        self.assertEqual('htb', class1.name)
        self.assertEqual({'rate': '768kbit', 'ceil': '1mbit'}, class1.params)


class TestFilter(unittest.TestCase):

    def test_wishful_api(self):
        Qdisc._major_counter = 1
        qdisc = Qdisc('htb', None, default=99)
        klass = QdiscClass('htb', qdisc, rate='384kbit')
        filter = Filter('u32', qdisc, cond='ip dport 5001 0xffff', flownode=klass)
        # FIXME: check something here?
        #expected = "tc filter add dev $DEV parent 2:1 protocol ip prio 1 u32 match ip dport 5001 0xffff flowid 1:1"
        #filter.cmd_repr()
        # filter = chain.add_filter('basic', cond=cond, flowid=htbclass)
        # filter = chain.add_filter('u32', cond='ip dport 5001 0xffff', flowid=htbclass)

CONFIG_SAMPLE = """\
[sym-4g]
iface lo
clear
dclass tcp:8000-8080:512mbit:2%
dclass udp:22000-24999:768kbit:2%
 
[sym-3g]
iface lo
clear
dclass tcp:8000-8080:128mbit:8%
dclass udp:22000-24999:96kbit:8%
"""


class TestTcFileTarget(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, TcFileTarget)

    def test_creation_iface(self):
        target = TcFileTarget(Interface('veth11'))
        self.assertEqual('veth11-egress.tc', target._filename)

    def test_creation_iface_direction(self):
        target = TcFileTarget(Interface('veth12'), DIR_INGRESS)
        self.assertEqual('veth12-ingress.tc', target._filename)

    def test_clear(self):
        iface = Interface('veth13')
        target = TcFileTarget(iface)
        target.clear()
        expected = ['tc qdisc del dev veth13 root']
        self.assertEqual(expected, target._commands)

    def test_add_qdisc(self):
        Qdisc._major_counter = 1
        iface = Interface('veth14')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=14)
        self.assertIsInstance(root_qdisc, Qdisc)
        self.assertEqual(['tc qdisc add dev veth14 root handle 1:0 htb default 14'], target._commands)

    def test_add_class(self):
        Qdisc._major_counter = 1
        iface = Interface('veth15')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=15)
        class1 = target.add_class('htb', root_qdisc, rate='256kbit', ceil='512kbit')
        self.assertIsInstance(class1, QdiscClass)
        expected = [
            'tc qdisc add dev veth15 root handle 1:0 htb default 15',
            'tc class add dev veth15 parent 1:0 classid 1:1 htb ceil 512kbit rate 256kbit',
        ]
        self.assertEqual(expected, target._commands)

    def test_add_filter(self):
        Qdisc._major_counter = 1
        iface = Interface('veth16')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=16)
        class1 = target.add_class('htb', root_qdisc, rate='256kbit', ceil='512kbit')
        filter = target.add_filter('u32', root_qdisc, 'ip dport 5001 0xffff', flownode=class1)
        # TODO: assert filter props
        expected = [
            'tc qdisc add dev veth16 root handle 1:0 htb default 16',
            'tc class add dev veth16 parent 1:0 classid 1:1 htb ceil 512kbit rate 256kbit',
            'tc filter add dev veth16 parent 1:0 protocol ip prio 1 u32 match ip dport 5001 0xffff flowid 1:1',
        ]
        self.assertEqual(expected, target._commands)

    def _test_install(self):
        self.fail("implement")

    def _test_wishful_api(self):
        # FIXME: no longer works!
        Qdisc._major_counter = 1
        iface = Interface('veth17')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=17)
        class1 = target.add_class('htb', root_qdisc, rate='768kbit')
        qdisc = target.add_qdisc('htb', class1, rate='384kbit')
        result = target.install(verbose=True)
        expected = """\
tc qdisc add dev veth17 root handle 1:0 htb default 17
tc class add dev veth17 parent 1:0 classid 1:1 htb rate 768kbit
tc qdisc add dev veth17 parent 1:1 handle 2:0 htb rate 384kbit"""
        self.assertEqual(expected, result)


class TestInterface(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, Interface)

    def test_creation(self):
        iface = Interface('veth21')
        self.assertEqual('veth21', iface.name)

    def test_ingress(self):
        iface = Interface('veth22')
        self.assertIsInstance(iface.ingress, ITarget)

    def test_egress(self):
        iface = Interface('veth23')
        self.assertIsInstance(iface.egress, ITarget)

    def test_ingress_is_not_egress(self):
        iface = Interface('veth24')
        self.assertIsNot(iface.ingress, iface.egress)

    def wishful_api(self):
        Qdisc._major_counter = 1
        iface = Interface('veth0')
        root_qdisc1 = iface.ingress.set_root_qdisc('htb', default=90)
        class1 = iface.ingress.add_class('htb', root_qdisc1, rate='1024kbit')
        iface.ingress.add_qdisc('htb', class1, rate='512kbit')
        root_qdisc2 = iface.egress.set_root_qdisc('htb', default=95)
        class2 = iface.egress.add_class('htb', root_qdisc2, rate='256kbit')
        iface.egress.add_qdisc('htb', class2, rate='128kbit')
        # let's see what we've done:
        result = iface.install(DIR_EGRESS, verbose=True)
        expected = """\
tc qdisc add dev veth0 root handle 1:0 htb default 95
tc class add dev veth0 parent 1:0 classid 1:1 htb rate 128kbit
tc qdisc add dev veth0 parent 1:1 handle 2:0 htb rate 64kbit"""
        self.assertEqual(expected, result)


class TestTrafficControl(unittest.TestCase):

    def test_get_iface(self):
        TrafficControl.init()
        iface1 = TrafficControl.get_iface('iface')
        iface2 = TrafficControl.get_iface('iface')
        self.assertIs(iface1, iface2)

    def _test_wishful_api(self):
        # FIXME: no longer works!
        TrafficControl.init()
        eth0 = TrafficControl.get_iface('eth0')
        eth0.egress.clear()
        eth0.egress.shape_dports(range='8000-9080', rate='512kbit', loss='7%')  # pylint: disable=no-member
        expected = """\
tc qdisc del dev eth0 root
tc qdisc add dev eth0 root handle 1:0 htb
tc class add dev eth0 parent 1:0 classid 1:1 htb rate 512kbit
tc qdisc add dev eth0 parent 1:1 handle 2:0 netem limit 1000000000 loss 7%
tc filter add dev eth0 parent 1:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 7999) and cmp(u16 at 2 layer transport lt 9081)" flowid 1:1"""
        result = eth0.egress.install(verbose=True)
        #print(expected)
        #print(result)
        self.assertEqual(expected, result)


class TestConfigParser(unittest.TestCase):

    def test_creation_default(self):
        ConfigParser()

    def test_creation_w_stream(self):
        buff = io.StringIO()
        ConfigParser(buff)

    def test_creation_w_filename(self):
        ConfigParser("/etc/pyltc.conf")

    def test_creation_w_wrong_type(self):
        self.assertRaises(TypeError, ConfigParser, object())

    def test_parse(self):
        buff = io.StringIO(CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--iface', 'lo', '--clear', '--dclass', 'tcp:8000-8080:512mbit:2%', '--dclass', 'udp:22000-24999:768kbit:2%']
        self.assertEqual(expected, conf.section('sym-4g'))
        # TODO: check the other profile
        # TODO: check with non-existing profile
        #print(flush=True)
        #print(expected, flush=True)
        #print(conf.section('sym-4g'), flush=True)

    def test_parse_filename(self):
        # TODO: implement
        pass

    def test_parse_stream(self):
        # TODO: implement
        pass

    def wishful_api(self):
        buff = io.StringIO()
        config = ConfigParser()
        config.parse_stream(buff)
        #print() # -> a list with all argumets; multiple choises are in a list
        expected = ['--iface', 'lo', '--clear', 'dclass', 'dclass tcp:8000-8080:512mbit:2%', 'dclass', 'udp:22000-24999:768kbit:2%']
        self.assertEqual(expected, config.section('sym-3g'))


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2 or sys.argv[1] != 'test':
        try:
            main(sys.argv[1:])
        except MisconfigurationError as err:
            name = sys.argv[0].split(os.sep)[-1]  # TODO: make this a constant
            print(name, ": error: bad arguments: ", str(err).rstrip("."),". Try -h/--help.", sep="")
            sys.exit(2)
    else:
        sys.argv = sys.argv[:1]
        unittest.main()
