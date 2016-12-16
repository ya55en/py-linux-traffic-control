"""
Unit tests for the commandline utility module.

"""

import unittest
from subprocess import TimeoutExpired

from pyltc.device import Interface
from pyltc.target import TcCommandTarget
from pyltc.util.cmdline import CommandLine, CommandFailed


class TestCommandFailed(unittest.TestCase):

    def test_creation_default(self):
        self.assertRaises(TypeError, CommandFailed)

    def test_creation_w_command(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        exc = CommandFailed(cmd)
        self.assertEqual("Command failed: '/bin/false' (rc=1)", str(exc))

    def test_creation_w_non_command_fails(self):
        self.assertRaises(AssertionError, CommandFailed, "STRING")

    def test_returncode(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        exc = CommandFailed(cmd)
        self.assertEqual(cmd.returncode, exc.returncode)
        self.assertIsNotNone(exc.returncode)


class TestCommandLine(unittest.TestCase):

    def test_creation_default(self):
        self.assertRaises(TypeError, CommandLine)

    def test_creation_cmd_line(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual("/bin/true", cmd.cmdline)
        self.assertFalse(cmd._ignore_errors)

    def test_creation_cmd_line_ignore_errors(self):
        cmd = CommandLine("/bin/true", ignore_errors=True)
        self.assertEqual("/bin/true", cmd.cmdline)
        self.assertTrue(cmd._ignore_errors)

    def test_execute_simple(self):
        cmd = CommandLine("/bin/true")
        obj = cmd.execute()
        self.assertEqual(0, cmd.returncode)
        self.assertIs(cmd, obj)
        self.assertEqual("", cmd.stdout)
        self.assertEqual("", cmd.stderr)

    def test_execute_complex_success(self):
        cmd = CommandLine("echo ALPHA55 BRAVO55").execute()
        self.assertEqual(0, cmd.returncode)
        self.assertEqual("ALPHA55 BRAVO55", cmd.stdout.rstrip())
        self.assertEqual("", cmd.stderr)

    def test_ignore_error_false(self):
        cmd = CommandLine("/bin/false", ignore_errors=False)
        self.assertRaises(CommandFailed, cmd.execute)
        cmd = CommandLine("/bin/false")
        self.assertRaises(CommandFailed, cmd.execute)

    def test_ignore_error_true(self):
        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        self.assertNotEqual(0, cmd.returncode)
        self.assertIsNotNone(cmd.returncode)

    def test_timeout(self):
        cmd = CommandLine("/bin/sleep 1", ignore_errors=True)
        self.assertRaises(TimeoutExpired, cmd.execute, timeout=0.1)

    def test_wishful_api(self):
        cmd = CommandLine("echo ALPHA BRAVO").execute()
        self.assertEqual(0, cmd.returncode)
        self.assertEqual("ALPHA BRAVO", cmd.stdout.rstrip())
        self.assertEqual("", cmd.stderr)

        cmd = CommandLine("/bin/false", ignore_errors=False)
        self.assertRaises(Exception, cmd.execute)

        cmd = CommandLine("/bin/false", ignore_errors=True).execute()
        self.assertNotEqual(0, cmd.returncode)

    def test_construct_cmd_list_case_1(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual(['one', 'two', 'three'], cmd._construct_cmd_list('one two three'))

    def test_construct_cmd_list_case_2(self):
        cmd = CommandLine("/bin/true")
        self.assertEqual(['one', 'two three', 'four'], cmd._construct_cmd_list('one "two three" four'))

    def test_construct_cmd_list_case_3(self):
        cmd = CommandLine("/bin/true")
        expected = ['one', 'two three', 'four', 'five', 'three words together', 'last']
        result = cmd._construct_cmd_list('one "two three" four five "three words together" "last"')
        self.assertEqual(expected, result)

    def test_construct_cmd_list_case_4(self):
        cmd = CommandLine("/bin/true")
        self.assertRaises(RuntimeError, cmd._construct_cmd_list, 'asd " asd"123"')

    def test_real(self):
        # FIXME: revisit this; add checks
        iface = Interface('veth15')
        target = TcCommandTarget(iface)
        target._commands = ['echo TEST_TEST', '/bin/true', 'echo (._. )']
        #target.install(verbosity=True)
        target.install(verbose=False)


if __name__ == '__main__':
    unittest.main()
