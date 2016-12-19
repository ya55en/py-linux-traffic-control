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

COMMENTED_CONFIG_SAMPLE = """\
[sym-4g]
iface lo    # the network intreface
clear       ; clears the qdisc chain

# dclass stands for destination port classifier
dclass tcp:8000-8080:512mbit:2%
dclass udp:22000-24999:768kbit:2%

; not that leadong (or trailing) whitespaces should create no issues.
 [sym-3g]
 iface lo
 clear
 ; just to mention that there is also sclass option
 ; which means source port classifier
dclass tcp:8000-8080:128mbit:8%
dclass udp:22000-24999:96kbit:8%

[empty]
  ; the empty seciton is expected not to break parsing
  # and appear as a section with no keys.
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


class TestCommentedConfig(unittest.TestCase):

    def find_comment_start(self, line):
        """Identical to the find_comment_start() inner function in ConfigParser.parse()."""
        return min((line + "#").find("#"), (line + ";").find(";"))

    def test__find_comment_start(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff)
        line = "one # two";  self.assertEqual("one ", line[:self.find_comment_start(line)])
        line = "one ; two";  self.assertEqual("one ", line[:self.find_comment_start(line)])
        line = "one, two";  self.assertEqual("one, two", line[:self.find_comment_start(line)])
        line = " ;one, two #hop";  self.assertEqual(" ", line[:self.find_comment_start(line)])
        line = "; one, two #hop";  self.assertEqual("", line[:self.find_comment_start(line)])
        line = "# one, two ;hop";  self.assertEqual("", line[:self.find_comment_start(line)])

    def test_parse_profile_1(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--iface', 'lo', '--clear', '--dclass', 'tcp:8000-8080:512mbit:2%', '--dclass', 'udp:22000-24999:768kbit:2%']
        self.assertEqual(expected, conf.section('sym-4g'))

    def test_parse_profile_2(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--iface', 'lo', '--clear', '--dclass', 'tcp:8000-8080:128mbit:8%', '--dclass', 'udp:22000-24999:96kbit:8%']
        self.assertEqual(expected, conf.section('sym-3g'))

    def test_parse_profile_3(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        self.assertEqual([], conf.section('empty'))


if __name__ == '__main__':
    unittest.main()
