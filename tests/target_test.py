"""
Unit tests for the PyLTC target module.

"""

import unittest

from pyltc import DIR_INGRESS, DIR_EGRESS
from pyltc.device import Interface
from pyltc.struct import Qdisc, QdiscClass
from pyltc.target import TcTarget, TcFileTarget


class DummyTcTarget(TcTarget):
    """A dummy subclass to allow for testing the abstract ``TcTarget`` class."""
    def install(self):
        pass


class TestTcTarget(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, DummyTcTarget)

    def test_creation_iface(self):
        iface = Interface('veth51')
        target = DummyTcTarget(iface)
        self.assertIs(iface, target._iface)
        self.assertEqual(DIR_EGRESS, target._direction)
        self.assertFalse(bool(target._commands))

    def test_creation_iface_direction(self):
        iface = Interface('veth52')
        target = DummyTcTarget(iface, DIR_INGRESS)
        self.assertIs(iface, target._iface)
        self.assertEqual(DIR_INGRESS, target._direction)


class TestTcFileTarget(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, TcFileTarget)

    def test_configure_default_direction(self):
        target = TcFileTarget(Interface('veth11'))
        target.configure()
        self.assertEqual('veth11-egress.tc', target._filename)

    def test_test_configure_direction_ingress(self):
        target = TcFileTarget(Interface('veth12'), DIR_INGRESS)
        target.configure()
        self.assertEqual('veth12-ingress.tc', target._filename)

    def test_configure_custom_filename(self):
        target = TcFileTarget(Interface('veth12a'), DIR_INGRESS)
        target.configure(filename='custom-filename.tc')
        self.assertEqual('custom-filename.tc', target._filename)

    def test_clear(self):
        iface = Interface('veth13')
        target = TcFileTarget(iface)
        target.clear()
        expected = ['tc qdisc del dev veth13 root']
        self.assertEqual(expected, target._commands)

    def test_add_qdisc(self):
        Qdisc._major_counter = 1
        iface = Interface('veth14')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=14)
        self.assertIsInstance(root_qdisc, Qdisc)
        self.assertEqual(['tc qdisc add dev veth14 root handle 1:0 htb default 14'], target._commands)

    def test_add_class(self):
        Qdisc._major_counter = 1
        iface = Interface('veth15')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=15)
        class1 = target.add_class('htb', root_qdisc, rate='256kbit', ceil='512kbit')
        self.assertIsInstance(class1, QdiscClass)
        expected = [
            'tc qdisc add dev veth15 root handle 1:0 htb default 15',
            'tc class add dev veth15 parent 1:0 classid 1:1 htb ceil 512kbit rate 256kbit',
        ]
        self.assertEqual(expected, target._commands)

    def test_add_filter(self):
        Qdisc._major_counter = 1
        iface = Interface('veth16')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=16)
        class1 = target.add_class('htb', root_qdisc, rate='256kbit', ceil='512kbit')
        filter = target.add_filter('u32', root_qdisc, 'ip dport 5001 0xffff', flownode=class1)
        # TODO: assert filter props
        expected = [
            'tc qdisc add dev veth16 root handle 1:0 htb default 16',
            'tc class add dev veth16 parent 1:0 classid 1:1 htb ceil 512kbit rate 256kbit',
            'tc filter add dev veth16 parent 1:0 protocol ip prio 1 u32 match ip dport 5001 0xffff flowid 1:1',
        ]
        self.assertEqual(expected, target._commands)

    def _test_install(self):
        self.fail("implement")

    def _test_wishful_api(self):
        # FIXME: no longer works!
        Qdisc._major_counter = 1
        iface = Interface('veth17')
        target = TcFileTarget(iface)
        root_qdisc = target.add_qdisc('htb', None, default=17)
        class1 = target.add_class('htb', root_qdisc, rate='768kbit')
        qdisc = target.add_qdisc('htb', class1, rate='384kbit')
        result = target.install(verbose=True)
        expected = """\
tc qdisc add dev veth17 root handle 1:0 htb default 17
tc class add dev veth17 parent 1:0 classid 1:1 htb rate 768kbit
tc qdisc add dev veth17 parent 1:1 handle 2:0 htb rate 384kbit"""
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
