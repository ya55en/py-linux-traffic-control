"""
Core classes for the py-linux-traffic-control library.

The Linux Traffic Control Structure (LTCS) consists of qudiscs, classes
and filters, as recognized by the tc utility [1].

The core module defines objects for each of these hierarchy elements that helps
build the relationships and automatically generate reference ids.

[1] https://en.wikipedia.org/wiki/Tc_(Linux)

"""

from abc import ABC

from pyltc.util.counter import Counter


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
        self._filter_prio = Counter(start=1)

    @property
    def filter_prio(self):
        return next(self._filter_prio)

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

    _major_counter = None

    @classmethod
    def init(cls):
        cls._major_counter = Counter(start=1)

    def __init__(self, name, parent, **kw):
        """Initializes this node.
           See LtcNode.__init__() docstring.
        """
        super(Qdisc, self).__init__(name, parent, **kw)
        self._major = next(self._major_counter)
        self._minor = 0
        self._classes_minor = Counter(start=1)

    def new_class_id(self):
        """Creates and returns a new LTC classid as a (major, minor) tuple.
           The major is the same as the major of this qdisc object.

           :return: tuple - (int, int) tuple with (major, minor)
        """
        return (self._major, next(self._classes_minor))

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

    _handle_counter = None

    @classmethod
    def init(cls):
        cls._handle_counter = Counter(start=1)

    def __init__(self, name, parent, cond, flownode, prio=None, handle=None):
        """Initializer.
        :param name: string - the filter name (e.g. 'u32')
        :param parent: LtcNode - the parent to "attach" this filter to
        :param cond: string - the filter match condition
        :param flownode: LtcNode - the node to direct the mathing flow at
        :param prio: int - the priority level
        :param handle: int - the handle  # FIXME: check the type, we may need to putput hex format
        """
        self._name = name  # the filtertype
        self._parent = parent
        self._cond = cond
        self._flownode = flownode
        self._prio = prio if prio else parent.filter_prio
        self._handle = handle if handle else next(self._handle_counter)

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @property
    def nodeid(self):
        return self._handle

    @property
    def flowid(self):
        return self._flownode.nodeid

    @property
    def prio(self):
        return self._prio

    @property
    def handle(self):
        return '0x{:x}'.format(self._handle)
