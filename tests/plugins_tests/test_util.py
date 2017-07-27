"""
Unit tests for the pyltc helper stuff.

"""
import unittest
from configparser import ParsingError

from pyltc.plugins.simnet.util import BranchParser


class TestBranchParser(unittest.TestCase):

    def test_creation_default_fails(self):
        self.assertRaises(TypeError, BranchParser)

    def test_creation_one_argument_fails(self):
        self.assertRaises(TypeError, BranchParser, 'tcp:sport:all:512kbit:5%')

    def test_creation_proper_works(self):
        BranchParser('tcp:sport:all:512kbit:5%', download=True)
        BranchParser('tcp:sport:all:512kbit:5%', upload=True)
        BranchParser('tcp:sport:all:512kbit:5%', download=True, upload=False)
        BranchParser('tcp:sport:all:512kbit:5%', download=False, upload=True)
        BranchParser('tcp:lport:all:512kbit:5%', upload=True)
        BranchParser('tcp:rport:all:512kbit:5%', download=True)

    def test_creation_download_n_upload_fails(self):
        self.assertRaises(TypeError, BranchParser, 'tcp:sport:all:512kbit:5%', download=True, upload=True)
        self.assertRaises(TypeError, BranchParser, 'tcp:sport:all:512kbit:5%', download=False, upload=False)
        self.assertRaises(TypeError, BranchParser, 'tcp:sport:all:512kbit:5%')

    def test_dontcare_creation_passes(self):
        BranchParser('tcp:sport:all:512kbit:5%', download=True, upload=True, dontcare=True)
        BranchParser('tcp:sport:all:512kbit:5%', download=False, upload=False, dontcare=True)
        BranchParser('tcp:sport:all:512kbit:5%', dontcare=True)

    def test_standard_case(self):
        branch = BranchParser('tcp:sport:all:512kbit:5%', download=True)
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': 'all', 'rate': '512kbit', 'loss': '5%'}
        self.assertEqual(expected, branch.as_dict())
        self.assertEqual('tcp', branch.protocol)
        self.assertEqual('sport', branch.porttype)
        self.assertEqual('all', branch.range)
        self.assertEqual('512kbit', branch.rate)
        self.assertEqual('5%', branch.loss)

    def test_lport_cases(self):
        branch = BranchParser('tcp:lport:all:512kbit:5%', upload=True)
        self.assertEqual('sport', branch.porttype)
        branch = BranchParser('tcp:lport:all:512kbit:5%', download=True)
        self.assertEqual('dport', branch.porttype)

    def test_rport_cases(self):
        branch = BranchParser('tcp:rport:all:512kbit:5%', upload=True)
        self.assertEqual('dport', branch.porttype)
        branch = BranchParser('tcp:rport:all:512kbit:5%', download=True)
        self.assertEqual('sport', branch.porttype)

    def test_protocol_tcp(self):
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': 'all', 'rate': '512kbit', 'loss': '5%'}
        self.assertEqual(expected, BranchParser('tcp:sport:all:512kbit:5%', upload=True).as_dict())
        expected = {'protocol': 'tcp', 'porttype': 'dport', 'range': 'all', 'rate': '6mbit', 'loss': None}
        self.assertEqual(expected, BranchParser('tcp:dport:all:6mbit', upload=True).as_dict())
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': 'all', 'rate': None, 'loss': '14%'}
        self.assertEqual(expected, BranchParser('tcp:sport:all:14%', upload=True).as_dict())
        expected = {'protocol': 'tcp', 'porttype': None, 'range': 'all', 'rate': None, 'loss': '14%'}
        self.assertEqual(expected, BranchParser('tcp:all:14%', upload=True).as_dict())
        expected = {'protocol': 'udp', 'porttype': None, 'range': 'all', 'rate': '13mbit', 'loss': None}
        self.assertEqual(expected, BranchParser('udp:all:13mbit', upload=True).as_dict())

    def test_tcp_range(self):
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': '8000-8006', 'rate': '3gbit', 'loss': '27%'}
        self.assertEqual(expected, BranchParser('tcp:sport:8000-8006:3gbit:27%', upload=True).as_dict())
        expected = {'protocol': 'tcp', 'porttype': 'dport', 'range': '9000-9006', 'rate': '7bit', 'loss': None}
        self.assertEqual(expected, BranchParser('tcp:dport:9000-9006:7bit', upload=True).as_dict())
        expected = {'protocol': 'tcp', 'porttype': 'sport', 'range': '10000-10006', 'rate': None, 'loss': '2%'}
        self.assertEqual(expected, BranchParser('tcp:sport:10000-10006:2%', upload=True).as_dict())

    def test_udp_single(self):
        expected = {'protocol': 'udp', 'porttype': 'sport', 'range': '12000', 'rate': '64mbit', 'loss': '16%'}
        self.assertEqual(expected, BranchParser('udp:sport:12000:64mbit:16%', upload=True).as_dict())
        expected = {'protocol': 'udp', 'porttype': 'dport', 'range': '13000', 'rate': '35kbit', 'loss': None}
        self.assertEqual(expected, BranchParser('udp:dport:13000:35kbit', upload=True).as_dict())
        expected = {'protocol': 'udp', 'porttype': 'sport', 'range': '14000', 'rate': None, 'loss': '89%'}
        self.assertEqual(expected, BranchParser('udp:sport:14000:89%', upload=True).as_dict())

    def test_raises_parsing_error(self):
        self.assertRaises(ParsingError, BranchParser, 'tcp:dport:all', upload=True)
        self.assertRaises(ParsingError, BranchParser, 'udp:8000-8008:128kbit', upload=True)
        self.assertRaises(ParsingError, BranchParser, 'sport:5002-5005:1mbit', upload=True)
        self.assertRaises(ParsingError, BranchParser, 'tcp:dport:12gbit:3%', upload=True)
        self.assertRaises(ParsingError, BranchParser, 'tcp:dport:12gbit:3%', upload=True)

    def test_excersize_parsing_error(self):
        errors = list()
        for klass, arg1, arg2 in ((BranchParser, 'tcp:dport:all', True),
                        (BranchParser, 'udp:8000-8008:128kbit', True),
                        (BranchParser, 'sport:5002-5005:1mbit', True),
                        (BranchParser, 'tcp:dport:12gbit:3%', True),
                        (BranchParser, 'tcp:dport:12gbit:3%', True)):
            try:
                klass(arg1, arg2)
            except ParsingError as err:
                errors.append(str(err))
        expected = ['Source contains parsing errors: "Either RATE, JITTER or both must be present in \'tcp:dport:all\'"', 'Source contains parsing errors: "Port type not found in \'udp:8000-8008:128kbit\' (may be omitted only if range is \'all\')"', 'Source contains parsing errors: "Invalid upload/download argument: \'sport:5002-5005:1mbit\'"', 'Source contains parsing errors: "Invalid upload/download argument: \'tcp:dport:12gbit:3%\'"', 'Source contains parsing errors: "Invalid upload/download argument: \'tcp:dport:12gbit:3%\'"']
        self.assertEqual(expected, errors)
        # printing to see how error messages look like:
        # for err in errors:
        #     print(err)


if __name__ == '__main__':
    unittest.main()
