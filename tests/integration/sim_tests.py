"""
Simulation tests for pyltc.
We generate tc commands without executing them, which allows for quick regression testing.

TODO: A larger test suite is comming soon, and it will be machine generated.

"""

import unittest
import sys
from os.path import abspath, normpath, dirname, join as pjoin

REPO_ROOT = normpath(abspath(pjoin(dirname(__file__), "..", "..")))

if not REPO_ROOT in sys.path:
    sys.path.append(REPO_ROOT)

from pyltc.core.netdevice import DeviceManager
from tests.util.base import LtcSimulateTargetRun


class TestPyLtcFake(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        DeviceManager.shutdown_module('ifb')

    @classmethod
    def tearDownClass(cls):
        DeviceManager.shutdown_module('ifb')

    def test_upload_simple_tcp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'tcp:dport:9000-9010:512kbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 2:0 classid 2:1 htb rate 512kbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 8999) and cmp(u16 at 2 layer transport lt 9011)" flowid 2:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_upload_single_port_tcp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo1', '-c', '--upload', 'tcp:dport:9100:1mbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo1 root',
            'tc qdisc add dev lo1 root handle 1:0 htb',
            'tc class add dev lo1 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo1 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo1 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo1 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo1 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo1 parent 1:2 handle 3:0 htb',
            'tc class add dev lo1 parent 2:0 classid 2:1 htb rate 1mbit',
            'tc filter add dev lo1 parent 2:0 protocol ip prio 1 u32 match ip dport 9100 0xffff flowid 2:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_upload_simple_udp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'udp:dport:9200-9210:786kbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 3:0 classid 3:1 htb rate 786kbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 9199) and cmp(u16 at 2 layer transport lt 9211)" flowid 3:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_upload_single_port_udp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'udp:dport:9300:2mbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 3:0 classid 3:1 htb rate 2mbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 1 u32 match ip dport 9300 0xffff flowid 3:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_upload_all_rage(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'tcp:all:128kbit', 'udp:all:24mbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 128kbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 24mbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_upload_complex(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'tcp:dport:9700:2mbit', 'tcp:sport:9800-9820:4mbit:3%', 'udp:sport:9900-9910:786kbit:10%', 'udp:dport:9999:1gbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 2:0 classid 2:1 htb rate 2mbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 1 u32 match ip dport 9700 0xffff flowid 2:1',
            'tc class add dev lo parent 2:0 classid 2:2 htb rate 4mbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 2 basic match "cmp(u16 at 0 layer transport gt 9799) and cmp(u16 at 0 layer transport lt 9821)" flowid 2:2',
            'tc qdisc add dev lo parent 2:2 handle 4:0 netem limit 1000000000 loss 3%',
            'tc class add dev lo parent 3:0 classid 3:1 htb rate 786kbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 1 basic match "cmp(u16 at 0 layer transport gt 9899) and cmp(u16 at 0 layer transport lt 9911)" flowid 3:1',
            'tc qdisc add dev lo parent 3:1 handle 5:0 netem limit 1000000000 loss 10%',
            'tc class add dev lo parent 3:0 classid 3:2 htb rate 1gbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 2 u32 match ip dport 9999 0xffff flowid 3:2'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_simple_tcp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'tcp:dport:9400-9410:1mbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb',
            'tc class add dev ifb0 parent 2:0 classid 2:1 htb rate 1mbit',
            'tc filter add dev ifb0 parent 2:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 9399) and cmp(u16 at 2 layer transport lt 9411)" flowid 2:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_single_port_tcp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'tcp:sport:9500:6%'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb',
            'tc class add dev ifb0 parent 2:0 classid 2:1 htb rate 15gbit',
            'tc filter add dev ifb0 parent 2:0 protocol ip prio 1 u32 match ip sport 9500 0xffff flowid 2:1',
            'tc qdisc add dev ifb0 parent 2:1 handle 4:0 netem limit 1000000000 loss 6%'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_simple_udp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'udp:dport:9600-9610:786gbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb',
            'tc class add dev ifb0 parent 3:0 classid 3:1 htb rate 786gbit',
            'tc filter add dev ifb0 parent 3:0 protocol ip prio 1 basic match "cmp(u16 at 2 layer transport gt 9599) and cmp(u16 at 2 layer transport lt 9611)" flowid 3:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_single_port_udp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'udp:sport:9600:2mbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb',
            'tc class add dev ifb0 parent 3:0 classid 3:1 htb rate 2mbit',
            'tc filter add dev ifb0 parent 3:0 protocol ip prio 1 u32 match ip sport 9600 0xffff flowid 3:1'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_all_rage(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'tcp:all:128gbit', 'udp:all:224kbit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 128gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 224kbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_download_complex(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--download', 'tcp:dport:10000:1mbit', 'tcp:sport:10100-10120:384kbit:7%', 'udp:sport:10200-10210:512mbit:10%', 'udp:dport:10300:12bit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 1:0 htb',
            'tc class add dev ifb0 parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev ifb0 parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev ifb0 parent 1:1 handle 2:0 htb',
            'tc qdisc add dev ifb0 parent 1:2 handle 3:0 htb',
            'tc class add dev ifb0 parent 2:0 classid 2:1 htb rate 1mbit',
            'tc filter add dev ifb0 parent 2:0 protocol ip prio 1 u32 match ip dport 10000 0xffff flowid 2:1',
            'tc class add dev ifb0 parent 2:0 classid 2:2 htb rate 384kbit',
            'tc filter add dev ifb0 parent 2:0 protocol ip prio 2 basic match "cmp(u16 at 0 layer transport gt 10099) and cmp(u16 at 0 layer transport lt 10121)" flowid 2:2',
            'tc qdisc add dev ifb0 parent 2:2 handle 4:0 netem limit 1000000000 loss 7%',
            'tc class add dev ifb0 parent 3:0 classid 3:1 htb rate 512mbit',
            'tc filter add dev ifb0 parent 3:0 protocol ip prio 1 basic match "cmp(u16 at 0 layer transport gt 10199) and cmp(u16 at 0 layer transport lt 10211)" flowid 3:1',
            'tc qdisc add dev ifb0 parent 3:1 handle 5:0 netem limit 1000000000 loss 10%',
            'tc class add dev ifb0 parent 3:0 classid 3:2 htb rate 12bit',
            'tc filter add dev ifb0 parent 3:0 protocol ip prio 2 u32 match ip dport 10300 0xffff flowid 3:2'
        ]
        self.assertEqual(expected, fake_test.result)

    def test_both_complex(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--upload', 'tcp:dport:9700:2mbit', 'tcp:sport:9800-9820:4mbit:3%', 'udp:sport:9900-9910:786kbit:10%', 'udp:dport:9999:1gbit', '--download', 'tcp:dport:10000:1mbit', 'tcp:sport:10100-10120:384kbit:7%', 'udp:sport:10200-10210:512mbit:10%', 'udp:dport:10300:12bit'])
        fake_test.run()
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 15gbit',
            'tc class add dev lo parent 1:0 classid 1:2 htb rate 15gbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 1:1',
            'tc filter add dev lo parent 1:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 1:2',
            'tc qdisc add dev lo parent 1:1 handle 2:0 htb',
            'tc qdisc add dev lo parent 1:2 handle 3:0 htb',
            'tc class add dev lo parent 2:0 classid 2:1 htb rate 2mbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 1 u32 match ip dport 9700 0xffff flowid 2:1',
            'tc class add dev lo parent 2:0 classid 2:2 htb rate 4mbit',
            'tc filter add dev lo parent 2:0 protocol ip prio 2 basic match "cmp(u16 at 0 layer transport gt 9799) and cmp(u16 at 0 layer transport lt 9821)" flowid 2:2',
            'tc qdisc add dev lo parent 2:2 handle 4:0 netem limit 1000000000 loss 3%',
            'tc class add dev lo parent 3:0 classid 3:1 htb rate 786kbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 1 basic match "cmp(u16 at 0 layer transport gt 9899) and cmp(u16 at 0 layer transport lt 9911)" flowid 3:1',
            'tc qdisc add dev lo parent 3:1 handle 5:0 netem limit 1000000000 loss 10%',
            'tc class add dev lo parent 3:0 classid 3:2 htb rate 1gbit',
            'tc filter add dev lo parent 3:0 protocol ip prio 2 u32 match ip dport 9999 0xffff flowid 3:2',
            'tc qdisc del dev lo ingress',
            'tc qdisc add dev lo handle ffff:0 ingress',
            'tc filter add dev lo parent ffff:0 protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0',
            'tc qdisc del dev ifb0 root',
            'tc qdisc add dev ifb0 root handle 6:0 htb',
            'tc class add dev ifb0 parent 6:0 classid 6:1 htb rate 15gbit',
            'tc class add dev ifb0 parent 6:0 classid 6:2 htb rate 15gbit',
            'tc filter add dev ifb0 parent 6:0 protocol ip prio 1 u32 match ip protocol 6 0xff flowid 6:1',
            'tc filter add dev ifb0 parent 6:0 protocol ip prio 2 u32 match ip protocol 17 0xff flowid 6:2',
            'tc qdisc add dev ifb0 parent 6:1 handle 7:0 htb',
            'tc qdisc add dev ifb0 parent 6:2 handle 8:0 htb',
            'tc class add dev ifb0 parent 7:0 classid 7:1 htb rate 1mbit',
            'tc filter add dev ifb0 parent 7:0 protocol ip prio 1 u32 match ip dport 10000 0xffff flowid 7:1',
            'tc class add dev ifb0 parent 7:0 classid 7:2 htb rate 384kbit',
            'tc filter add dev ifb0 parent 7:0 protocol ip prio 2 basic match "cmp(u16 at 0 layer transport gt 10099) and cmp(u16 at 0 layer transport lt 10121)" flowid 7:2',
            'tc qdisc add dev ifb0 parent 7:2 handle 9:0 netem limit 1000000000 loss 7%',
            'tc class add dev ifb0 parent 8:0 classid 8:1 htb rate 512mbit',
            'tc filter add dev ifb0 parent 8:0 protocol ip prio 1 basic match "cmp(u16 at 0 layer transport gt 10199) and cmp(u16 at 0 layer transport lt 10211)" flowid 8:1',
            'tc qdisc add dev ifb0 parent 8:1 handle 10:0 netem limit 1000000000 loss 10%',
            'tc class add dev ifb0 parent 8:0 classid 8:2 htb rate 12bit',
            'tc filter add dev ifb0 parent 8:0 protocol ip prio 2 u32 match ip dport 10300 0xffff flowid 8:2'
        ]
        self.assertEqual(expected, fake_test.result)


if __name__ == '__main__':
    unittest.main()
