"""
Facade for the PyLTC framework.

"""
from pyltc.device import Interface
from pyltc.struct import Qdisc, Filter


class TrafficControl(object):
    """A facade static class for convenient use of the pyltc framework."""

    _iface_map = None

    @classmethod
    def init(cls):
        cls._iface_map = dict()
        Qdisc._major_counter = 1
        Filter._prio_counter = 1
        Filter._handle_counter = 1

    @classmethod
    def get_iface(cls, ifname, target_factory=None):
        try:
            return cls._iface_map[ifname]
        except KeyError:
            iface = Interface(ifname, target_factory)
            cls._iface_map[ifname] = iface
            return iface
