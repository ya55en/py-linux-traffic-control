"""
Unit tests for the target chain builders module.

"""
import unittest
from unittest import mock
import io
import time

from pyltc.core import DIR_EGRESS, DIR_INGRESS
from pyltc.core.ltcnode import Qdisc, QdiscClass, Filter
from pyltc.core.netdevice import NetDevice
from pyltc.core.target import TcTarget, TcFileTarget, TcCommandTarget


class DummyTcTarget(TcTarget):
    """Dummy traget that does nothing on ``marshal()``."""
    def marshal(self):
        pass


class TestTcTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Qdisc.init()
        Filter.init()

    def test_as_subcommand_standard_case(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil='512kbit')
        self.assertEqual('htb ceil 512kbit rate 256kbit', TcTarget.as_subcommand(qd))

    def test_as_subcommand_no_args(self):
        qd = Qdisc('htb', None)
        self.assertEqual('htb', TcTarget.as_subcommand(qd))

    def test_as_subcommand_arg_is_none(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil=None)
        self.assertEqual('htb rate 256kbit', TcTarget.as_subcommand(qd))

    def test_creation_no_args_fails(self):
        self.assertRaises(TypeError, DummyTcTarget)
        self.assertRaises(TypeError, DummyTcTarget, 'foo')

    def test_creation_w_ifname_direction_ok(self):
        target = DummyTcTarget(NetDevice('bazz0'), DIR_EGRESS)
        # check that configure() default is called:
        self.assertIsNotNone(target._verbose)
        self.assertFalse(target._verbose)

    def test_creation_w_ifdevice_direction_ok(self):
        dev = NetDevice('bazz1')
        DummyTcTarget(dev, DIR_EGRESS)

    def test_clear_on_egress(self):
        target = DummyTcTarget(NetDevice('bazz0'), DIR_EGRESS)
        target.clear()
        expected = ['tc qdisc del dev bazz0 root']
        self.assertEqual(expected, target._commands)

    def test_clear_on_ingress(self):
        target = DummyTcTarget(NetDevice('bazz0'), DIR_INGRESS)
        target.clear()
        expected = ['tc qdisc del dev bazz0 ingress']
        self.assertEqual(expected, target._commands)

    def test_configure(self):
        target = DummyTcTarget(NetDevice('bazz0'), DIR_INGRESS)
        target.configure(verbose=True)
        self.assertTrue(target._verbose)

    def test_add_qdisc(self):
        Qdisc.init()  # reset the qdisc major counter
        target = DummyTcTarget(NetDevice('bar1'), DIR_EGRESS)
        target.add_qdisc('htb', None, rate='111kbit')
        expected = ['tc qdisc add dev bar1 root handle 1:0 htb rate 111kbit']
        self.assertEqual(expected, target._commands)

    def test_set_root_qdisc_egress(self):
        Qdisc.init()  # reset the qdisc major counter
        target = DummyTcTarget(NetDevice('bar2'), DIR_EGRESS)
        target.set_root_qdisc('htb', rate='222kbit')
        expected = ['tc qdisc add dev bar2 root handle 1:0 htb rate 222kbit']
        self.assertEqual(expected, target._commands)

    def test_set_root_qdisc_ingress(self):
        Qdisc.init()  # reset the qdisc major counter
        target = DummyTcTarget(NetDevice('bar3'), DIR_INGRESS)
        target.set_root_qdisc('htb', rate='333kbit')
        expected = ['tc qdisc add dev bar3 ingress handle 1:0 htb rate 333kbit']
        self.assertEqual(expected, target._commands)

    def test_add_class(self):
        Qdisc.init()  # reset the qdisc major counter
        target = DummyTcTarget(NetDevice('bar4'), DIR_EGRESS)
        qdisc = Qdisc('htb', None, default=99)
        target.add_class('htb', qdisc, rate='444kbit')
        expected = ['tc class add dev bar4 parent 1:0 classid 1:1 htb rate 444kbit']
        self.assertEqual(expected, target._commands)

    def test_add_filter(self):
        Qdisc.init()  # reset the qdisc major counter
        target = DummyTcTarget(NetDevice('bar5'), DIR_EGRESS)
        qdisc = Qdisc('htb', None, default=99)
        qclass = QdiscClass('htb', qdisc, rate='555kbit')
        target.add_filter('u32', qdisc, 'ip dport 5001 0xffff', qclass, prio=9)
        expected = ['tc filter add dev bar5 parent 1:0 protocol ip prio 9 u32 match ip dport 5001 0xffff flowid 1:1']
        self.assertEqual(expected, target._commands)


class TestTcFileTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Qdisc.init()

    def test_creation_ok(self):
        target = TcFileTarget(NetDevice('bar11'), DIR_EGRESS)
        self.assertIsNone(target._filename)

    def test_configure_default(self):
        target = TcFileTarget(NetDevice('bar22'), DIR_EGRESS)
        target.configure()
        self.assertIsNotNone(target._filename)

    def test_configure_custom(self):
        target = TcFileTarget(NetDevice('bar33'), DIR_EGRESS)
        target.configure(filename='mysamplefilename.tc')
        self.assertEqual('mysamplefilename.tc', target._filename)

    @mock.patch('pyltc.core.target.open')
    @mock.patch('pyltc.core.target.print')
    def test_marshal_when_not_configured(self, fake_print, fake_open):
        target = TcFileTarget(NetDevice('bar44'), DIR_EGRESS)
        target.set_root_qdisc('htb', default=144)
        target.marshal()
        fake_print.assert_not_called()
        fake_open.assert_not_called()

    @mock.patch('pyltc.core.target.open')
    @mock.patch('pyltc.core.target.print')
    def test_marshal_when_configured(self, fake_print, fake_open):
        fake_open.return_value = buff = io.StringIO()
        target = TcFileTarget(NetDevice('bar55'), DIR_EGRESS)
        timestamp = time.time()
        target.configure(verbose=True, filename='/tmp/tempfile-{}'.format(timestamp))
        target.set_root_qdisc('htb', default=155)
        target.marshal()
        expected = "tc qdisc add dev bar55 root handle 1:0 htb default 155"
        fake_print.assert_called_once_with(expected)
        fake_open.assert_called_once_with('/tmp/tempfile-{}'.format(timestamp), 'w')
        #self.assertEqual(expected, buff.getvalue())  # TODO: provide a buff that retains value even after close()


class TestTcCommandTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Qdisc.init()

    def test_creation_proper(self):
        TcCommandTarget(NetDevice('foo11'), DIR_EGRESS)

    @mock.patch('pyltc.core.target.CommandLine')
    def test_marshal(self, fake_command_line):
        target = TcCommandTarget(NetDevice('foo12'), DIR_EGRESS)
        target.clear()
        rootqd = target.set_root_qdisc('htb')
        target.add_class('htb', rootqd, rate='512kbit', ceil='512kbit')
        target.marshal()
        calls = [
            mock.call('tc qdisc del dev foo12 root', ignore_errors=True, sudo=True, verbose=False),
            mock.call().execute(),
            mock.call('tc qdisc add dev foo12 root handle 1:0 htb', ignore_errors=False, sudo=True, verbose=False),
            mock.call().execute(),
            mock.call('tc class add dev foo12 parent 1:0 classid 1:1 htb ceil 512kbit rate 512kbit',
                      ignore_errors=False, sudo=True, verbose=False),
            mock.call().execute(),
        ]
        fake_command_line.assert_has_calls(calls)


if __name__ == '__main__':
    unittest.main()
