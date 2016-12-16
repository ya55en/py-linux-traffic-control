"""
Core classes for the py-linux-traffic-control library.

The Linux Traffic Control Structure (LTCS) consists of qudiscs, classes
and filters, as recognized by the tc utility [1].

The core module defines objects for each of these hierarchy elements that helps
build the relationships and automatically generate reference ids.

[1] https://en.wikipedia.org/wiki/Tc_(Linux)

"""

from abc import ABC


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
        sorted_seq = sorted(self._params.items(), key=lambda v: v[0])
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
