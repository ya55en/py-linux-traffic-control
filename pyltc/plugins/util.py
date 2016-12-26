import re
from configparser import ParsingError

regex = re.compile(r'^(tcp|udp):(all|\d{1,5}\-\d{1,5}|\d{1,5})(:\d+[a-z]{3,4})?(:\d{1,3}%)?$')

def parse_branch(branch_str):
    branch = {}
    match = regex.match(branch_str)
    if not (match.group(3) or match.group(4)):
        raise ParsingError('Either rate, loss, or both must be provided.')

    branch['protocol'] = match.group(1)
    branch['range'] = match.group(2)
    branch['rate'] = match.group(3).lstrip(':') if match.group(3) else match.group(3)
    branch['loss'] = match.group(4).lstrip(':') if match.group(4) else match.group(4)

    return branch


import unittest

class TestParseBranch(unittest.TestCase):

    def test_tcp_all(self):
        expected = {'protocol': 'tcp', 'range': 'all', 'rate': '512kbit', 'loss': '5%'}
        self.assertEqual(expected, parse_branch('tcp:all:512kbit:5%'))
        expected = {'protocol': 'tcp', 'range': 'all', 'rate': '6mbit', 'loss': None}
        self.assertEqual(expected, parse_branch('tcp:all:6mbit'))
        expected = {'protocol': 'tcp', 'range': 'all', 'rate': None, 'loss': '14%'}
        self.assertEqual(expected, parse_branch('tcp:all:14%'))
        self.assertRaises(ParsingError, parse_branch, 'tcp:all')

    def test_tcp_range(self):
        expected = {'protocol': 'tcp', 'range': '8000-8006', 'rate': '3gbit', 'loss': '27%'}
        self.assertEqual(expected, parse_branch('tcp:8000-8006:3gbit:27%'))
        expected = {'protocol': 'tcp', 'range': '9000-9006', 'rate': '7bit', 'loss': None}
        self.assertEqual(expected, parse_branch('tcp:9000-9006:7bit'))
        expected = {'protocol': 'tcp', 'range': '10000-10006', 'rate': None, 'loss': '2%'}
        self.assertEqual(expected, parse_branch('tcp:10000-10006:2%'))
        self.assertRaises(ParsingError, parse_branch, 'tcp:11000-11006')

    def test_udp_single(self):
        expected = {'protocol': 'udp', 'range': '12000', 'rate': '64mbit', 'loss': '16%'}
        self.assertEqual(expected, parse_branch('udp:12000:64mbit:16%'))
        expected = {'protocol': 'udp', 'range': '13000', 'rate': '35kbit', 'loss': None}
        self.assertEqual(expected, parse_branch('udp:13000:35kbit'))
        expected = {'protocol': 'udp', 'range': '14000', 'rate': None, 'loss': '89%'}
        self.assertEqual(expected, parse_branch('udp:14000:89%'))
        self.assertRaises(ParsingError, parse_branch, 'tcp:15000')

if __name__ == '__main__':
    unittest.main()
