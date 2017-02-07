"""
Simple examples of using ``pyltc`` framework from within python.

"""

from pyltc.core.facade import TrafficControl

# We will replace the default target builder with one that only prints commands on stdout:
from pyltc.core.tfactory import printing_target_factory

# Required: initializes the state of the framework:
TrafficControl.init()

# We get an object that represents the network interface eth0:
iface = TrafficControl.get_interface('lo', target_factory=printing_target_factory)

# The ITarget.clear() method builds a command that removes any previously attached
# qdiscs to the egress root hook of the Linux kernel.
iface.egress.clear()

# We now attach a qdisc which is going to be the root qdisc for the egress chain:
rootqd = iface.egress.set_root_qdisc('htb')

# We create a qdisc class attached to the root qdisc. kw arguments are passed
# direvtly to the qdisc in the form 'key1 value1 key2 value2'.
qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')

# We create a u32 filter with condition "ip protocol 17 0xff" attached to the root qdisc
# and directing mathching packets to the qdisc class we just created above:
filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)

# Marshalling the commands built for our case will simply dump them on stdout, as the
# factory define above -- ``tc_file_target_factory`` -- does only that.
iface.egress.marshal()

# Use pyltc.core.tfactory.default_target_factory to configure the framework to use
# TcCommandTarget, which will durung ``marshal()`` actually execute those commands.
# Note that you need root privileges to configure the kernel.
