"""
Unit tests for the PyLTC facade module.

"""

import unittest

from pyltc.device import Interface
from pyltc.facade import TrafficControl


class TestTrafficControl(unittest.TestCase):

    def test_get_iface(self):
        TrafficControl.init()
        iface1 = TrafficControl.get_iface('iface')
        iface2 = TrafficControl.get_iface('iface')
        self.assertIsInstance(iface1, Interface)
        self.assertIs(iface1, iface2)

    def _test_wishful_api(self):
        # FIXME: no longer works!
        TrafficControl.init()
        eth0 = TrafficControl.get_iface('eth0')
        eth0.egress.clear()
        eth0.egress.shape_dports(range='8000-9080', rate='512kbit', loss='7%')  # pylint: disable=no-member
        expected = """\
tc qdisc del dev eth0 root
tc qdisc add dev eth0 root handle 1:0 htb
tc class add dev eth0 parent 1:0 classid 1:1 htb rate 512kbit
tc qdisc add dev eth0 parent 1:1 handle 2:0 netem limit 1000000000 loss 7%
tc filter add dev eth0 parent 1:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 7999) and cmp(u16 at 2 layer transport lt 9081)" flowid 1:1"""
        result = eth0.egress.install(verbose=True)
        #print(expected)
        #print(result)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
