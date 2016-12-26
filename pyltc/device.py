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

    @classmethod
    def new_instance(cls, name, target_factory=default_target_factory):
        """
        TODO: document
        """
        if name is None:
            return MagicMock()
        return cls(name, target_factory)

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

        :param direction - string - the direction chain (DIR_EGRESS or DIR_INGRESS)
        """
        accepted_values = (DIR_EGRESS, DIR_INGRESS)
        assert direction in accepted_values, "direction must be one of {!r} (got {!r})" \
                                              .format(accepted_values, direction)
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
