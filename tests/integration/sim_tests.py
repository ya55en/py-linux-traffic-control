"""
Simulation tests for pyltc.
We tc commands without executing them, which allows for quick regression testing.

"""

import unittest

from tests.util.base import LtcSimulateTargetRun


class TestPyLtcFake(unittest.TestCase):

    def test_simple_tcp(self):
        fake_test = LtcSimulateTargetRun(['tc', '-i', 'lo', '-c', '--dclass', 'tcp:10100-10110:512kbit'])
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
            'tc filter add dev lo parent 2:0 protocol ip prio 3 basic match "cmp(u16 at 2 layer transport gt 10099) and cmp(u16 at 2 layer transport lt 10111)" flowid 2:1'
        ]
        self.assertEqual(expected, fake_test.result)


if __name__ == '__main__':
    unittest.main()
