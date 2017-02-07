"""
A bit more complex example of using ``pyltc`` framework from within python.
See ``simple.py`` module for detailed comments on the basic setup.

IMPORTANT: Requires sudo permissions in oreder to set up an ifb device.

"""

from pyltc.core.facade import TrafficControl
from pyltc.core.netdevice import DeviceManager

# Use any factory that suits your goal or omit this to use the default command-executing tc factory:
from pyltc.core.tfactory import printing_target_factory

TrafficControl.init()

# This target factory provides a target that only prints on stdout:
iface = TrafficControl.get_interface('lo', target_factory=printing_target_factory)

# Setting up an ifb device for the ingress control
# (We need a convenience method to ease this setup!)
ifbdev_name = 'ifb1'

# This one may raise "AssertionError: Device already exists: 'ifb0'" -- try wiht ifb1 (or ifb2, etc.)
DeviceManager.ensure_device(ifbdev_name)
ifbdev = TrafficControl.get_interface(ifbdev_name, target_factory=printing_target_factory)

iface.ingress.set_redirect(iface, ifbdev)

# Configuring and marshal the egress tc chain:
iface.egress.clear()
rootqd = iface.egress.set_root_qdisc('htb')
qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')
filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
iface.egress.marshal()

# Configuring and marshal the egress tc chain:
iface.ingress.clear()
rootqd = iface.ingress.set_root_qdisc('htb')
qdclass = iface.ingress.add_class('htb', rootqd, rate='384kbit')
filter = iface.ingress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
iface.ingress.marshal()
