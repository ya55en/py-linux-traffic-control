"""
Network device entities module.

"""
from unittest.mock import MagicMock

from pyltc import DIR_EGRESS, DIR_INGRESS
from pyltc.target import default_target_factory


class Interface(object):
    """
    Represents a network interface device with a name and an egress and ingress
    LTC chains.
    """

    def __init__(self, name, target_factory=None):
        """
        Initializes this interface object. See default_target_factory for
        details about the target_factory argument.

        :param name: string - the name of the network device, e.g. 'eth0'
        :param target_factory: function - implements the default_target_factory
                               signature.
        """
        self._name = name
        if not target_factory:
            target_factory = default_target_factory
        self._egress_chain = target_factory(self, DIR_EGRESS)
        self._ingress_chain = target_factory(self, DIR_INGRESS)
        self._ifbdev = None

    def set_ingress_device(self, ifbdev):
        #self._ingress_chain.set_ifb_redirect(self, ifbdev)
        ifbdev.set_redirect(self)
        #self._ingress_chain = ifbdev.egress
        self._ifbdev = ifbdev

    @classmethod
    def new_instance(cls, name, target_factory=None):
        """
        TODO: document
        """
        if name is None:
            return MagicMock()
        if target_factory is None:
            target_factory = default_target_factory
        return cls(name, target_factory)

    def setup(self, ipaddr=None):
        """Issues necessary commands to setup the device. By default does nothing
        as we expect the device to have been set up already."""

    @property
    def name(self):
        """Returns the name of this interface."""
        return self._name

    @property
    def ingress(self):
        """Returns the ingress chain builder for this interface.
        :return: ITarget - the ingress chain target builder
        """
        if self._ifbdev:
            return self._ifbdev._egress_chain   # TODO: or self._ifbdev.egress ?
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

        :param direction - string - the direction chain (DIR_EGRESS or DIR_INGRESS)
        """
        accepted_values = (DIR_EGRESS, DIR_INGRESS)
        assert direction in accepted_values, "direction must be one of {!r} (got {!r})" \
                                              .format(accepted_values, direction)
        if direction is None:
            self.egress.install(*args, **kw)
            self.ingress.install(*args, **kw)
            return
        if direction == DIR_EGRESS:
            self.egress.install(*args, **kw)
            return
        if direction == DIR_INGRESS:
            self.ingress.install(*args, **kw)
            return
        raise RuntimeError("UNREACHABLE!")


class IfbDevice(Interface):
    """Represents an IFB (Intermediate Functional Block) pseudo-network device.
    Used to allow for more precise simulation of network conditins for ingress traffic.

    See https://wiki.linuxfoundation.org/networking/ifb for details.
    """

    def set_redirect(self, pridev):
        """Sets redirect directives that instruct forwarding all ingress traffic on ``pridev`` interface
        to this device.

        :param pridev: ``Interface`` - the primary interface to be controlled
        """
        #iface.ingress.add_root_qdisc('configure its ingress to forward to my egress')
        #iface.ingress_forward = self.egress
          ##iface.forward_ingress(self)  # this is going to add proper ingress root and remember an ingress-related reference to self

        cmd1 = "tc qdisc add dev {pridev} handle ffff:0 ingress"
        cmd2 = ("tc filter add dev {pridev} parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress"
                " redirect dev {ifbdev}")
        args = {
            'pridev': pridev.name,
            'ifbdev': self.name,
        }
        self._egress_chain._commands.append(cmd1.format(**args))
        self._egress_chain._commands.append(cmd2.format(**args))



import unittest


class TestIfbInterface(unittest.TestCase):
    pass
