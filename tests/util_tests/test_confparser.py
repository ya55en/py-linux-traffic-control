"""
Unit tests for the confparser module.

"""

import unittest
import io

from pyltc.util.confparser import ConfigParser


CONFIG_SAMPLE = """\
[sym-4g]
interface lo
clear
upload tcp:dclass:8000-8080:512mbit:2%
  udp:sclass:9000:1gbit
  tcp:sclass:9100-9190:128bit:15%

[sym-3g]
interface lo
clear
upload tcp:dclass:8000-8080:2%
download tcp:sclass:6000-6060:512kbit
  udp:dclass:7000:768kbit
  tcp:all:3mbit:9%
  tcp:dclass:9100-9190:15kbit
"""

COMMENTED_CONFIG_SAMPLE = """\
[sym-4g]
interface lo    # the network intreface
clear       ; clears the qdisc chain

# upload stands for egress-related shaping
upload tcp:sclass:3000-3003:512kbit
  tcp:dclass:4004:64mbit
[sym-3g]
interface lo
clear
; just to mention that there is also a download option
; which means ingress-related
download udp:dclass:5000-5050:6gbit:8%
; note that leading whitespaces should only be used as continuing the last line.
upload udp:dclass:5000-5050:6gbit:8%
  tcp:sclass:15000:12%
  udp:all:6gbit:512mbit

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

    def test_preparse_typical(self):
        input_str = """\
[section-1]
download tcp:dport:8000-8099:111kbit:1%
upload tcp:dport:20000-30000:222kbit:2%
  tcp:dport:8000-8099:333bit
  tcp:dport:8000-8099:444kbit:4%
"""
        buff = io.StringIO(input_str)
        conf = ConfigParser(buff)
        lines = list()
        for line in conf._preparse():
            lines.append(line)
        expected = ['[section-1]', 'download tcp:dport:8000-8099:111kbit:1%', 'upload tcp:dport:20000-30000:222kbit:2% tcp:dport:8000-8099:333bit tcp:dport:8000-8099:444kbit:4%']
        self.assertEqual(expected, lines)

    def test_preparse_raises(self):
        input_str = """\
  [section-1]
upload tcp:dport:20000-30000:222kbit:2%
  tcp:dport:8000-8099:444kbit:4%
"""
        buff = io.StringIO(input_str)
        conf = ConfigParser(buff)
        try:
            for _ in conf._preparse():
                pass
        except RuntimeError as err:
            self.assertEqual('Invalid configuration file.', str(err))

    def test_parse(self):
        buff = io.StringIO(CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--interface', 'lo', '--clear', '--upload', 'tcp:dclass:8000-8080:512mbit:2%', 'udp:sclass:9000:1gbit', 'tcp:sclass:9100-9190:128bit:15%']
        self.assertEqual(expected, conf.section('sym-4g'))
        expected = ['--interface', 'lo', '--clear', '--upload', 'tcp:dclass:8000-8080:2%', '--download', 'tcp:sclass:6000-6060:512kbit', 'udp:dclass:7000:768kbit', 'tcp:all:3mbit:9%', 'tcp:dclass:9100-9190:15kbit']
        self.assertEqual(expected, conf.section('sym-3g'))
        # TODO: check with non-existing profile

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
        expected = ['--interface', 'lo', '--clear', '--download', 'tcp:sclass:6000-6060:512kbit', 'udp:dclass:7000:768kbit']
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
        line = "foo, bar, baz#";  self.assertEqual("foo, bar, baz", line[:self.find_comment_start(line)])
        line = "foo, bar, baz;";  self.assertEqual("foo, bar, baz", line[:self.find_comment_start(line)])
        line = "foo, bar, bazzz";  self.assertEqual("foo, bar, bazzz", line[:self.find_comment_start(line)])

    def test_strip_comments(self):
        input_str = """\
[section-1] # comment here
download tcp:dport:8000-8099:111kbit:1% ; comment # inside ; comment
upload tcp:dport:20000-30000:222kbit:2%
# comment only
# on multiple lines
; and different kinds
  tcp:dport:8000-8099:333bit
  tcp:dport:8000-8099:444kbit:4%
"""
        buff = io.StringIO(input_str)
        conf = ConfigParser(buff)
        lines = list()
        for line in conf._strip_comments():
            lines.append(line)
        expected = ['[section-1] ', 'download tcp:dport:8000-8099:111kbit:1% ', 'upload tcp:dport:20000-30000:222kbit:2%\n', '', '', '', '', '', '',  '  tcp:dport:8000-8099:333bit\n', '  tcp:dport:8000-8099:444kbit:4%\n']
        self.assertEqual(expected, lines)

    def test_parse_profile_1(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--interface', 'lo', '--clear', '--upload', 'tcp:sclass:3000-3003:512kbit', 'tcp:dclass:4004:64mbit']
        self.assertEqual(expected, conf.section('sym-4g'))

    def test_parse_profile_2(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        expected = ['--interface', 'lo', '--clear', '--download', 'udp:dclass:5000-5050:6gbit:8%', '--upload', 'udp:dclass:5000-5050:6gbit:8%', 'tcp:sclass:15000:12%', 'udp:all:6gbit:512mbit']
        self.assertEqual(expected, conf.section('sym-3g'))

    def test_parse_profile_3(self):
        buff = io.StringIO(COMMENTED_CONFIG_SAMPLE)
        conf = ConfigParser(buff).parse()
        self.assertIsInstance(conf, ConfigParser)
        self.assertEqual([], conf.section('empty'))


if __name__ == '__main__':
    unittest.main()
