"""
Unit tests for the pyltc.core module.

"""

import unittest
from pyltc.struct import Qdisc, QdiscClass, Filter


class TestQdisc(unittest.TestCase):

    def test_creation(self):
        from pyltc.struct import Qdisc
        Qdisc._major_counter = 1
        qd1 = Qdisc('htb', None, rate='256kbit')
        self.assertEqual('1:0', qd1.handle)
        qd2 = Qdisc('htb', None, rate='512kbit')
        self.assertEqual('2:0', qd2.handle)

    def test_parent(self):
        parent_qdisc = Qdisc('htb', None, rate='256kbit')
        parent_class = QdiscClass('htb', parent_qdisc, rate='768kbit')
        qdisc = Qdisc('htb', parent_class, rate='256kbit')
        self.assertIs(parent_class, qdisc.parent)

    def test_kw(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil='512kbit')
        self.assertEqual('htb', qd.name)
        self.assertEqual({'rate': '256kbit', 'ceil': '512kbit'}, qd.params)

    def test_cmd_repr(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil='512kbit')
        self.assertEqual('htb ceil 512kbit rate 256kbit', qd.cmd_repr())

    def test_cmd_repr_no_args(self):
        qd = Qdisc('htb', None)
        self.assertEqual('htb', qd.cmd_repr())

    def test_cmd_repr_arg_is_none(self):
        qd = Qdisc('htb', None, rate='256kbit', ceil=None)
        self.assertEqual('htb rate 256kbit', qd.cmd_repr())


class TestQdiscClass(unittest.TestCase):

    def test_creation(self):
        Qdisc._major_counter = 1
        parentqd = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parentqd, rate='768kbit')
        self.assertEqual('1:1', class1.classid)

    def test_parent(self):
        parent_qdisc = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parent_qdisc, rate='768kbit')
        self.assertIs(parent_qdisc, class1.parent)

    def test_kw(self):
        parentqd = Qdisc('htb', None, rate='256kbit')
        class1 = QdiscClass('htb', parentqd, rate='768kbit', ceil='1mbit')
        self.assertEqual('htb', class1.name)
        self.assertEqual({'rate': '768kbit', 'ceil': '1mbit'}, class1.params)


class TestFilter(unittest.TestCase):

    def test_wishful_api(self):
        Qdisc._major_counter = 1
        qdisc = Qdisc('htb', None, default=99)
        klass = QdiscClass('htb', qdisc, rate='384kbit')
        filter = Filter('u32', qdisc, cond='ip dport 5001 0xffff', flownode=klass)
        # FIXME: check something here?
        #expected = "tc filter add dev $DEV parent 2:1 protocol ip prio 1 u32 match ip dport 5001 0xffff flowid 1:1"
        #filter.cmd_repr()
        # filter = chain.add_filter('basic', cond=cond, flowid=htbclass)
        # filter = chain.add_filter('u32', cond='ip dport 5001 0xffff', flowid=htbclass)


if __name__ == '__main__':
    unittest.main()
