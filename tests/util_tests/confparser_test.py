"""
Unit tests for the confparser module.

"""

import unittest
import io

from pyltc.util.confparser import ConfigParser


CONFIG_SAMPLE = """\
[sym-4g]
iface lo
clear
dclass tcp:8000-8080:512mbit:2%
dclass udp:22000-24999:768kbit:2%

[sym-3g]
iface lo
clear
dclass tcp:8000-8080:128mbit:8%
dclass udp:22000-24999:96kbit:8%
"""


class TestConfigParser(unittest.TestCase):

    def test_creation_default(self):
        ConfigParser()

    def test_creation_w_stream(self):
        buff = io.StringIO()
        ConfigParser(buff)

    def test_creation_w_filename(self):
        ConfigParser("/etc/pyltc.conf")

    def test_creation_w_wrong_type(self):
        self.assertRaises(TypeError, ConfigParser, object())

    def test_parse(self):
        buff = io.StringIO(CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--iface', 'lo', '--clear', '--dclass', 'tcp:8000-8080:512mbit:2%', '--dclass', 'udp:22000-24999:768kbit:2%']
        self.assertEqual(expected, conf.section('sym-4g'))
        # TODO: check the other profile
        # TODO: check with non-existing profile
        #print(flush=True)
        #print(expected, flush=True)
        #print(conf.section('sym-4g'), flush=True)

    def test_parse_filename(self):
        # TODO: implement
        pass

    def test_parse_stream(self):
        # TODO: implement
        pass

    def wishful_api(self):
        buff = io.StringIO()
        config = ConfigParser()
        config.parse_stream(buff)
        #print() # -> a list with all argumets; multiple choises are in a list
        expected = ['--iface', 'lo', '--clear', 'dclass', 'dclass tcp:8000-8080:512mbit:2%', 'dclass', 'udp:22000-24999:768kbit:2%']
        self.assertEqual(expected, config.section('sym-3g'))


if __name__ == '__main__':
    unittest.main()
