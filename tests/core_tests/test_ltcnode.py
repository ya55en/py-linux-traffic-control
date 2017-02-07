"""
Unit tests for the ltcnode classes.

"""

import unittest
from pyltc.core.ltcnode import Qdisc, QdiscClass, Filter


class TestQdisc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Qdisc.init()

    def test_creation(self):
        Qdisc.init()
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


class TestQdiscClass(unittest.TestCase):

    def test_creation(self):
        Qdisc.init()
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

    @classmethod
    def setUpClass(cls):
        Qdisc.init()
        Filter.init()

    def test_prio_counter(self):
        qdisc = Qdisc('htb', None, default=99)
        klass = QdiscClass('htb', qdisc, rate='384kbit')
        filter_1 = Filter('u32', qdisc, cond='ip dport 50011 0xffff', flownode=klass)
        filter_2 = Filter('u32', qdisc, cond='ip dport 50012 0xffff', flownode=klass)
        filter_3 = Filter('u32', qdisc, cond='ip dport 50013 0xffff', flownode=klass)
        self.assertEqual(1, filter_1.prio)
        self.assertEqual(2, filter_2.prio)
        self.assertEqual(3, filter_3.prio)

    def test_accessors(self):
        qdisc = Qdisc('htb', None, default=99)
        klass_1 = QdiscClass('htb', qdisc, rate='384kbit')
        filter = Filter('u32', qdisc, cond='ip dport 50021 0xffff', flownode=klass_1)
        self.assertEqual('u32', filter.name)
        self.assertIs(qdisc, filter.parent)
        self.assertEqual(1, filter.nodeid)
        self.assertEqual('0x1', filter.handle)
        self.assertEqual('1:1', filter.flowid)
        self.assertEqual(1, filter.prio)
        klass_2 = QdiscClass('htb', qdisc, rate='384kbit')
        filter = Filter('u32', qdisc, cond='ip dport 50022 0xffff', flownode=klass_2)
        self.assertEqual('u32', filter.name)
        self.assertIs(qdisc, filter.parent)
        self.assertEqual(2, filter.nodeid)
        self.assertEqual('0x2', filter.handle)
        self.assertEqual('1:2', filter.flowid)
        self.assertEqual(2, filter.prio)

    def wishful_api(self):
        qdisc = Qdisc('htb', None, default=99)
        klass = QdiscClass('htb', qdisc, rate='384kbit')
        filter = Filter('u32', qdisc, cond='ip dport 5001 0xffff', flownode=klass)
        # FIXME: check something here?
        #expected = "tc filter add dev $DEV parent 2:1 protocol ip prio 1 u32 match ip dport 5001 0xffff flowid 1:1"
        #filter.cmd_repr()
        # filter = chain.add_filter('basic', cond=cond, flowid=htbclass)
        # filter = chain.add_filter('u32', cond='ip dport 5001 0xffff', flowid=htbclass)
