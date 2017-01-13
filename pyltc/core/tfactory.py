"""
TODO: docstring

"""
from pyltc.core import DIR_EGRESS, DIR_INGRESS
from pyltc.core.target import TcCommandTarget


def default_target_factory(iface, direction, callback=None):
    """
    The default target factory. If no custom factory is provided to the
    framework, this factory is used by the Interface.__init__() method to
    connfigure its egress and ingress target builders.

    A custom target factory may be provided to the Interface.__init__() that
    returns a target instance (that is, a class implementing ITarget).

    As the ITarget interface limits the arguments at creation time, the
    ITarget.configure() method can be used to further configure a target object.

    :param iface: Interface - the interface object :param direction: string - a
                  string representing flow direction (DIR_EGRESS or DIR_INGRESS)
    :return: ITarget - the ITarget object created by this factory.
    """
    accepted_values = (DIR_EGRESS, DIR_INGRESS)
    assert direction in accepted_values, "direction must be one of {!r}".format(accepted_values)
    target = TcCommandTarget(iface, direction)
    if callback:
        target.configure(callback=callback)
    return target
