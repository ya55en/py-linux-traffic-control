"""
Target chain builders module.

Target chain builders are Bulder pattern objects implementing the ``ITarget`` interface
that accumulate setup instructions related to configuring the Linux kernel traffic
control.

There are to target chains for each interface: "egress" (or "root") for outgoing traffic and "ingress"
chain for incoming traffic.

This module provides exclusively tc-oriented targets, if which the default one is ``TcCommandTarget``
who's ``marshal()`` will attempt to actually execute the accumulated setups as ``tc`` commands and
thus actually configure the kernel with that setup.

The other implementations here may print the setup to a file or stdout and are useful for testing purposes.

Targets of the same "family" differ mainly in their ``marshal()`` where the "installing" behaviour is
implemented.

"""
from pyltc.core import ITarget, DIR_EGRESS, DIR_INGRESS
from pyltc.core.ltcnode import Qdisc, QdiscClass, Filter
from pyltc.util.cmdline import CommandLine, CommandFailed


class TcTarget(ITarget):
    """
    An abstract ``ITarget`` that builds a setup of ``tc`` commands to configure the Linux
    kernel traffic control.
    """

    @staticmethod
    def as_subcommand(ltcnode):
        """Represents this ltc node as a tc-compatible sub-command.

        :param ltcnode: LtcNode subclass - the object to represent as a sub-command
        :return: string - the tc-compatible sub-command, e.g. 'htb rate 256kbit'
        """
        if not ltcnode._params:
            return ltcnode._name
        sorted_seq = sorted(ltcnode._params.items(), key=lambda v: v[0])
        kwargs = " ".join(('{} {}'.format(key, value) for key, value in sorted_seq if value is not None))
        return '{} {}'.format(ltcnode._name, kwargs)

    def __init__(self, iface, direction):
        assert iface.__class__.__name__ == 'NetDevice', "Expected type NetDevice but got " + type(iface).__name__
        assert direction in (DIR_EGRESS, DIR_INGRESS)
        self._iface = iface
        self._direction = direction
        self._chain_name = 'ingress' if direction == DIR_INGRESS else 'root'
        self._commands = list()
        self._verbose = None
        self.configure()

    def clear(self):
        cmd = "tc qdisc del dev {} {}".format(self._iface.name, self._chain_name)
        self._commands.append(cmd)

    def configure(self, **kw):
        self._verbose = kw.pop('verbose', False)
        assert not kw, "excessive arguments to configure(): {!r}".format(kw)

    def add_qdisc(self, name, parent, **kw):
        qdisc = Qdisc(name, parent, **kw)
        cmd_params = {
            'iface': self._iface.name,
            'parent': 'parent ' + parent.classid if parent else self._chain_name,
            'handle': qdisc.handle,
            'qdisc_repr': self.as_subcommand(qdisc),
        }
        cmd = "tc qdisc add dev {iface} {parent} handle {handle} {qdisc_repr}".format(**cmd_params)
        self._commands.append(cmd)
        return qdisc

    def set_root_qdisc(self, name, **kw):
        return self.add_qdisc(name, None, **kw)

    def add_class(self, name, parent, **kw):
        qdisc_class = QdiscClass(name, parent, **kw)
        cmd_params = {
            'iface': self._iface.name,
            'parentid': parent.handle,
            'classid': qdisc_class.classid,
            'klass_repr': self.as_subcommand(qdisc_class),
        }
        cmd = "tc class add dev {iface} parent {parentid} classid {classid} {klass_repr}".format(**cmd_params)
        self._commands.append(cmd)
        return qdisc_class

    def add_filter(self, name, parent, cond, flownode, prio=None, handle=None):
        """Adds a filter to the TC structure. The filter representation is oversimplified,
        so for complex filters creation a different approach is needed (if any such are
        going to be used.)

        From the tc man page::

           tc filter [ add | change | replace ] dev DEV [ parent qdisc-id | root ]
           protocol protocol prio priority filtertype [ filtertype specific parameters ] flowid flow-id

        See ``Itarget.add_filter().``
        """
        filter = Filter(name, parent, cond, flownode, prio=prio, handle=handle)
        cmd_params = {
            'name': name,
            'iface': self._iface.name,
            'parentid': parent.nodeid,
            'cond': cond,
            'flowid': flownode.nodeid,
            'prio': filter.prio,
            'handle': filter.handle,
        }
        cmd = ("tc filter add dev {iface} parent {parentid} protocol ip prio {prio}"
               " {name} match {cond} flowid {flowid}").format(**cmd_params)
        self._commands.append(cmd)
        return filter

    def set_redirect(self, pridev, ifbdev):
        cmd1 = "tc qdisc add dev {pridev} handle ffff:0 ingress"
        cmd2 = ("tc filter add dev {pridev} parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress"
                " redirect dev {ifbdev}")
        args = {
            'pridev': pridev.name,
            'ifbdev': ifbdev.name,
        }
        self._commands.append(cmd1.format(**args))
        self._commands.append(cmd2.format(**args))


class PrintingTcTarget(TcTarget):
    """TcTarget sub-class suitable for demo purposes.
    On ``marshal()`` simply prints the content of the commands buffer to stdout.
    (We this way avoid sudo permissions while executing examples and tests.)

    Note that if your TcTarget sub-class is not configurable (as in this case)
    you can pass the class as a target factory, as it accepts the same
    arguments (``interface``, ``direction``).
    """

    def marshal(self):
        print("** PRINTING ONLY: tc", self._direction, "commands **")
        for cmd in self._commands:
            print(cmd)


class TcFileTarget(TcTarget):
    """An ``ITarget`` implementation that builds ``/sbin/tc`` compatible commands
    and finally represents them as a multi-line string or saves them into a file.
    """
    def __init__(self, iface, direction):
        # super(self.__class__, self).__init__(iface, direction)
        super(TcFileTarget, self).__init__(iface, direction)
        self._filename = None

    def configure(self,  **kw):
        filename = kw.pop('filename', None)
        if not filename:
            filename = "{}-{}.tc".format(self._iface.name, self._direction)
        self._filename = filename
        super(TcFileTarget, self).configure(**kw)

    def marshal(self):
        result = '\n'.join(self._commands)
        if self._verbose:
            print(result)
        if self._filename:
            with open(self._filename, 'w') as fhl:
                fhl.write(result + '\n')


class TcCommandTarget(TcTarget):
    """An ``ITarget`` implementation that builds ``/sbin/tc`` compatible commands
    and finally executes them against the kernel in order to configure its traffic
    control disciplines.
    """
    def __init__(self, iface, direction):
        super(TcCommandTarget, self).__init__(iface, direction)

    def _marshal(self):
        for idx, cmd_str in enumerate(self._commands):
            ignore_errs = (idx == 0 and " del" in cmd_str)  # removal failures are expected, ignore
            CommandLine(cmd_str, ignore_errors=ignore_errs, verbose=self._verbose, sudo=True).execute()

    def marshal(self):
        try:
            self._marshal()
        except CommandFailed as exc:
            print(exc)
