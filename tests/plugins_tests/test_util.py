"""
TODO: doc
"""
import unittest
from configparser import ParsingError

from pyltc.plugins.util import parse_branch


class TestParseBranch(unittest.TestCase):

    def test_tcp_all(self):
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': 'all', 'rate': '512kbit', 'loss': '5%'}
        self.assertEqual(expected, parse_branch('tcp:sport:all:512kbit:5%'))
        expected = {'protocol': 'tcp', 'porttype': 'dport', 'range': 'all', 'rate': '6mbit', 'loss': None}
        self.assertEqual(expected, parse_branch('tcp:dport:all:6mbit'))
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': 'all', 'rate': None, 'loss': '14%'}
        self.assertEqual(expected, parse_branch('tcp:sport:all:14%'))
        expected = {'protocol': 'tcp', 'porttype': None, 'range': 'all', 'rate': None, 'loss': '14%'}
        self.assertEqual(expected, parse_branch('tcp:all:14%'))
        expected = {'protocol': 'udp', 'porttype': None, 'range': 'all', 'rate': '13mbit', 'loss': None}
        self.assertEqual(expected, parse_branch('udp:all:13mbit'))

    def test_tcp_range(self):
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': '8000-8006', 'rate': '3gbit', 'loss': '27%'}
        self.assertEqual(expected, parse_branch('tcp:sport:8000-8006:3gbit:27%'))
        expected = {'protocol': 'tcp', 'porttype': 'dport', 'range': '9000-9006', 'rate': '7bit', 'loss': None}
        self.assertEqual(expected, parse_branch('tcp:dport:9000-9006:7bit'))
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': '10000-10006', 'rate': None, 'loss': '2%'}
        self.assertEqual(expected, parse_branch('tcp:sport:10000-10006:2%'))

    def test_udp_single(self):
        expected = {'protocol': 'udp', 'porttype': 'sport', 'range': '12000', 'rate': '64mbit', 'loss': '16%'}
        self.assertEqual(expected, parse_branch('udp:sport:12000:64mbit:16%'))
        expected = {'protocol': 'udp', 'porttype': 'dport', 'range': '13000', 'rate': '35kbit', 'loss': None}
        self.assertEqual(expected, parse_branch('udp:dport:13000:35kbit'))
        expected = {'protocol': 'udp', 'porttype': 'sport', 'range': '14000', 'rate': None, 'loss': '89%'}
        self.assertEqual(expected, parse_branch('udp:sport:14000:89%'))

    def test_assert_raises(self):
        self.assertRaises(ParsingError, parse_branch, 'tcp:dport:all')
        self.assertRaises(ParsingError, parse_branch, 'udp:8000-8008:128kbit')
        self.assertRaises(ParsingError, parse_branch, 'sport:5002-5005:1mbit')
        self.assertRaises(ParsingError, parse_branch, 'tcp:dport:12gbit:3%')
        self.assertRaises(ParsingError, parse_branch, 'tcp:dport:12gbit:3%')


if __name__ == '__main__':
    unittest.main()
