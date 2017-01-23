"""
TODO: doc
"""
import unittest

from pyltc.core.facade import TrafficControl
from tests.util.base import TcTestTarget


class TestWrapper(unittest.TestCase):

    def setUp(self):
        self.result = list()

    def our_callback(self, result):
        self.result = self.result + result

    def target_factory(self, iface, direction):
        return TcTestTarget(iface, direction, self.our_callback)

    def test_basic_case(self):
        TrafficControl.init()
        simnet = TrafficControl.get_plugin('simnet', self.target_factory)
        simnet.setup(upload=True, protocol='tcp', porttype='dport', range='8000-8080', rate='512kbit', jitter='7%')
        simnet.marshal()
        expected = [
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 2:0 classid 2:1 htb rate 512kbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 7999) and cmp(u16 at 2 layer transport lt 8081)" flowid 2:1',
            'tc qdisc add dev lo parent 2:1 handle 4:0 netem limit 1000000000 loss 7%',
        ]
        # for expline, resline in zip(expected, self.result):
        #     if expline != resline:
        #         print(expline)
        #         print(resline)
        self.assertEqual(expected, self.result)

    def test_complex_case(self):
        TrafficControl.init()
        simnet = TrafficControl.get_plugin('simnet', self.target_factory)
        simnet.configure(interface='lo1', ifbdevice='ifb0', clear=True)
        simnet.setup(upload=True, protocol='tcp', porttype='dport', range='8000-8080', rate='512kbit', jitter='7%')
        simnet.setup(upload=True, protocol='udp', porttype='sport', range='8100', rate='1mbit')
        simnet.setup(download=True, protocol='tcp', range='all', jitter='5%')
        simnet.setup(download=True, protocol='tcp', porttype='dport', range='8200-8220', rate='3gbit', jitter='3%')
        simnet.marshal()
        expected = [
            'tc qdisc del dev lo1 root',
            'tc qdisc add dev lo1 root handle 1:0 htb',
            'tc class add dev lo1 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo1 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo1 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo1 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo1 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo1 parent 1:2 handle 3:0 htb',
            'tc class add dev lo1 parent 2:0 classid 2:1 htb rate 512kbit',
            'tc filter add dev lo1 parent 2:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 7999) and cmp(u16 at 2 layer transport lt 8081)" flowid 2:1',
            'tc qdisc add dev lo1 parent 2:1 handle 4:0 netem limit 1000000000 loss 7%',
            'tc class add dev lo1 parent 3:0 classid 3:1 htb rate 1mbit',
            'tc filter add dev lo1 parent 3:0 protocol ip prio 1 u32 match ip sport 8100 0xffff flowid 3:1',
            'tc qdisc del dev lo1 ingress',
            'tc qdisc add dev lo1 handle ffff:0 ingress',
            'tc filter add dev lo1 parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 5:0 htb',
            'tc class add dev ifb0 parent 5:0 classid 5:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 5:0 classid 5:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 5:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 5:1',
            'tc filter add dev ifb0 parent 5:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 5:2',
            'tc qdisc add dev ifb0 parent 5:1 handle 6:0 htb',
            'tc qdisc add dev ifb0 parent 5:2 handle 7:0 htb',
            'tc class add dev ifb0 parent 6:0 classid 6:1 htb rate 3gbit',
            'tc filter add dev ifb0 parent 6:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 8199) and cmp(u16 at 2 layer transport lt 8221)" flowid 6:1',
            'tc qdisc add dev ifb0 parent 6:1 handle 8:0 netem limit 1000000000 loss 3%',
        ]
        # for expline, resline in zip(expected, self.result):
        #     if expline != resline:
        #         print(expline)
        #         print(resline)
        self.assertEqual(expected, self.result)

if __name__ == '__main__':
    unittest.main()
