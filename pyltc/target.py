"""
PyLTC targets module.

Targets are builders that interpret the structure consisting of elements
from the node.py module and finally produces a specific "installation" of this
structure. This "installation" is typically a series of tc commands [1] but
can be simply a text output file or a dump on the console. Custom targets
can be created. To do that, inherit and implement ITarget.

[1] https://en.wikipedia.org/wiki/Tc_(Linux)

"""

from abc import abstractmethod, ABC

from pyltc import DIR_EGRESS, DIR_INGRESS
from pyltc.struct import QdiscClass, Qdisc, Filter
from pyltc.util.cmdline import CommandFailed, CommandLine


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

    def clear(self, is_ingress=False):
        root_name = 'ingress' if is_ingress else 'root'
        cmd = "tc qdisc del dev {} {}".format(self._iface.name, root_name)
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
            # 'handle': filter._handle,
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
    compatible commands and finally executes them.
    """
    def __init__(self, iface, direction=DIR_EGRESS):
        super(TcCommandTarget, self).__init__(iface, direction=direction)

    def _install(self, verbose=False):
        for idx, cmd_str in enumerate(self._commands):
            should_ignore_errs = (idx == 0 and " del" in cmd_str)
            #if verbose:  # TODO: remove
            #    print("# {!s}".format(cmd_str))
            CommandLine(cmd_str, ignore_errors=should_ignore_errs).execute(verbose=verbose)

    def install(self, verbose=False):
        try:
            self._install(verbose=verbose)
        except CommandFailed as exc:
            print(exc)


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
