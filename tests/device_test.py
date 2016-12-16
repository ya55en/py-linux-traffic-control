"""
PyLTC device mosule unit tests.

"""
import unittest

from pyltc import DIR_EGRESS
from pyltc.device import Interface
from pyltc.struct import Qdisc
from pyltc.target import ITarget


class TestInterface(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, Interface)

    def test_creation(self):
        iface = Interface('veth21')
        self.assertEqual('veth21', iface.name)

    def test_sentinel(self):
        iface = Interface.new_instance(None)
        iface.ingress.clear()
        iface.egress.clear()
        iface.ingress.set_root_qdisc('foo')
        iface.egress.set_root_qdisc('foo')
        iface.ingress.add_class('bar', parent=None)
        iface.egress.add_class('bar', parent=None)
        iface.ingress.add_filter('hi')
        iface.egress.add_filter('lo')
        iface.ingress.install()
        iface.egress.install()

    def test_ingress(self):
        iface = Interface('veth22')
        self.assertIsInstance(iface.ingress, ITarget)

    def test_egress(self):
        iface = Interface('veth23')
        self.assertIsInstance(iface.egress, ITarget)

    def test_ingress_is_not_egress(self):
        iface = Interface('veth24')
        self.assertIsNot(iface.ingress, iface.egress)

    def wishful_api(self):
        Qdisc._major_counter = 1
        iface = Interface('veth0')
        root_qdisc1 = iface.ingress.set_root_qdisc('htb', default=90)
        class1 = iface.ingress.add_class('htb', root_qdisc1, rate='1024kbit')
        iface.ingress.add_qdisc('htb', class1, rate='512kbit')
        root_qdisc2 = iface.egress.set_root_qdisc('htb', default=95)
        class2 = iface.egress.add_class('htb', root_qdisc2, rate='256kbit')
        iface.egress.add_qdisc('htb', class2, rate='128kbit')
        # let's see what we've done:
        result = iface.install(DIR_EGRESS, verbose=True)
        expected = """\
tc qdisc add dev veth0 root handle 1:0 htb default 95
tc class add dev veth0 parent 1:0 classid 1:1 htb rate 128kbit
tc qdisc add dev veth0 parent 1:1 handle 2:0 htb rate 64kbit"""
        self.assertEqual(expected, result)
