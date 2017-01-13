"""
Target builder factories for the ``pyltc`` framework.

Target builders are objects implementing ``ITarget`` (see the ``pyltc.core.target``
package for the default implementations).  The main target builder flavor is
``TcTarget`` with two subclasses, representing a ``tc``-compatible commands target.

The ``tc`` command is part of the ``iproute2`` network utilities for Linux.
See http://man7.org/linux/man-pages/man8/tc.8.html for details about the ``tc``
command.

"""
from pyltc.core import DIR_EGRESS, DIR_INGRESS
from pyltc.core.target import TcCommandTarget, TcFileTarget


def default_target_factory(iface, direction, callback=None):
    """
    The default target factory. If no custom factory is provided to the
    framework, this factory is used by the ``NetDevice.new_instance()`` method
    to connfigure its egress and ingress target builders.

    A custom target factory may be provided to ``NetDevice.new_instance()`` that
    returns a target instance (that is, a class implementing ITarget).

    As the ITarget interface limits the arguments at creation time, the
    ITarget.configure() method can be used to further configure a target object.

    :param iface: NetDevice - the network device object
    :param direction: string - a string representing flow direction (DIR_EGRESS or DIR_INGRESS)
    :return: ITarget - the ITarget object created by this factory.
    :param callback: callable - a callback function to be called to complete this target configuration.
    :return: TcCommandTarget
    """
    accepted_values = (DIR_EGRESS, DIR_INGRESS)
    assert direction in accepted_values, "direction must be one of {!r}".format(accepted_values)
    target = TcCommandTarget(iface, direction)
    if callback:
        target.configure(callback=callback)
    return target


def tc_file_target_factory(iface, direction):
    """
    tc factory returning a new TcCommandTarget.

    :param iface: NetDevice - the network device object
    :param direction: string - a string representing flow direction (DIR_EGRESS or DIR_INGRESS)
    :param callback: callable - a callback function to be called to complete this target configuration.
    :return: TcCommandTarget - the ITarget object created by this factory.
    """
    accepted_values = (DIR_EGRESS, DIR_INGRESS)
    assert direction in accepted_values, "direction must be one of {!r}".format(accepted_values)
    target = TcFileTarget(iface, direction)
    target.configure(verbose=True)
    return target
