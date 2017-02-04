"""
Facade for the PyLTC framework.

"""
from pyltc.core.netdevice import NetDevice
from pyltc.core.ltcnode import Qdisc, Filter
from pyltc.plugins.simnet import SimNetPlugin


class TrafficControl(object):
    """A facade static class for convenient use of the pyltc framework."""

    _plugins_map = {
        'simnet': SimNetPlugin,
    }

    @classmethod
    def init(cls):
        NetDevice.init()
        Qdisc.init()
        Filter.init()

    @classmethod
    def get_interface(cls, ifname, target_factory=None):
        return NetDevice.get_device(ifname, target_factory)

    @classmethod
    def get_plugin(cls, name, target_factory=None):
        try:
            return cls._plugins_map[name](target_factory=target_factory)
        except KeyError:
            raise RuntimeError("Unknown plugin {!r}".format(name))
