"""
Examples for creating a custom target builder.

Our custom ``BufferTcTarget`` is suited to serve as a mock target during
test and example executions. It can be configured with a callback and on
``marshal()`` that callback is invoked with a single argument a copy of
the list with all tc commands accumulated.

"""
from pyltc.core import DIR_EGRESS
from pyltc.core.netdevice import NetDevice
from pyltc.core.target import TcTarget
from pyltc.core.facade import TrafficControl

TrafficControl.init()


class BufferTcTarget(TcTarget):
    """TcTarget sub-class suitable for test and demo purposes.
    Can be configured with a callback and on ``marshal()`` invokes that callback
    with a single argument being a copy of the accumulated commands list.
    """

    def configure(self, **kw):
        self._callback = kw.pop('callback', None)
        super(BufferTcTarget, self).configure(**kw)

    def marshal(self):
        if self._callback:
            self._callback(self._commands[:])


# _____________________________________________________________________
# Unit test code below

import unittest


class TestBufferTcTarget(unittest.TestCase):

    def setUp(self):
        self._command_list = None

    def test_creation(self):
        BufferTcTarget(NetDevice('lo'), DIR_EGRESS)

    def _the_callback(self, command_list):
        print("_the_callback() called with", command_list)
        self._command_list = command_list

    def test_typical_scenario(self):
        egress = BufferTcTarget(NetDevice('lo'), DIR_EGRESS)
        egress.configure(callback=self._the_callback)
        egress.clear()
        rootqd = egress.set_root_qdisc('htb')
        qdclass = egress.add_class('htb', rootqd, rate='384kbit')
        filter = egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
        egress.marshal()
        # check that the output is what we expect
        expected = [
            'tc qdisc del dev lo root',
            'tc qdisc add dev lo root handle 1:0 htb',
            'tc class add dev lo parent 1:0 classid 1:1 htb rate 384kbit',
            'tc filter add dev lo parent 1:0 protocol ip prio 1 u32 match ip protocol 17 0xff flowid 1:1',
        ]
        self.assertEqual(expected, self._command_list)


if __name__ == '__main__':
    unittest.main()
