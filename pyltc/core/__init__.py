"""
The PyLTC core package. (PyLTC is py-linux-traffic-control.)

"""
from abc import ABC, abstractmethod


DIR_EGRESS = 'egress'
DIR_INGRESS = 'ingress'


class ITarget(ABC):
    """Represents a target setup and marshaling method for LTC setup.

    Example: tc target (builds a set of tc commands for configuring the kernel)
    """

    @abstractmethod
    def __init__(self, iface, direction):
        """
        Initializer.

        :param iface: NetDevice - the network device object to configure TC on
        :param direction: string - a string representing flow direction
                          (one of ``core.DIR_EGRESS`` or ``core.DIR_INGRESS``)
        """

    @abstractmethod
    def configure(self, **kw):
        """Configures this builder after creation."""

    @abstractmethod
    def clear(self):
        """Builds a recipe for clearing the LTC chain."""

    @abstractmethod
    def set_root_qdisc(self, name, **kw):
        """
        Builds a recipe step for setting the root qdisc of the LTC chain and
        returns a Qdisc object with appropriate handle for further reference.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param kw: dict - any key-value arguments passed to the qdisc
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
        :param kw: dict - any key-value arguments passed to the qdisc
        :return: Qdisc - a newly created Qdisc object with a proper handler
        """

    @abstractmethod
    def add_class(self, name, parent, **kw):
        """
        Builds a recipe for adding a qdisc class to the LTC chain and returns
        a QdiscClass object with appropriate handle for further reference.

        :param name: string - the name by which the kernel knows this qdisc
                     (e.g. 'htb' or 'pfifo_fast')
        :param parent: Qdisc - a qdisc object to add this qdisc to
        :param kw: dict - any key-value arguments passed to the qdisc
        :return QdiscClass
        """

    @abstractmethod
    def add_filter(self, name, parent, cond, flownode, prio=None, handle=None):
        """
        Builds a recipe for adding a filter object to the LTC chain and returns
        a Filter object with appropriate handle for further reference.

        :param name: string - the name of this filter (e.g. 'u32')
        :param parent: Qdisc or QdiscClass - a qdisc or qdisc class object to attach this filter to
        :param cond: string - the match condition of this filter
        :param flownode: string - the id (classid or handle) of the node to process matching packets
        :param prio: int - priority level
        :param handle: int or hex - this filter's unique handle
        :return: Filter
        """

    @abstractmethod
    def marshal(self):
        """
        Marshals the kernel-configuring actions already built within this builder.
        Examples for 'marshaling': create a file with tc commands, or
        live execution of the tc commands to actually configure the kernel.
        """
