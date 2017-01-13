"""
Facade for the PyLTC framework.

"""
from pyltc.core.netdevice import NetDevice
from pyltc.core.ltcnode import Qdisc, Filter


class TrafficControl(object):
    """A facade static class for convenient use of the pyltc framework."""

    _iface_map = None

    @classmethod
    def init(cls):
        cls._iface_map = dict()
        Qdisc.init()
        Filter.init()

    @classmethod
    def get_iface(cls, ifname, target_factory=None):
        try:
            return cls._iface_map[ifname]
        except KeyError:
            cls._iface_map[ifname] = iface = NetDevice.new_instance(ifname, target_factory)
            return iface
