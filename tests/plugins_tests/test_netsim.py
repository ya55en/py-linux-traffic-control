import unittest

from pyltc.plugins.simnet import SimNetPlugin


class TestNetSim(unittest.TestCase):

    def test_configure_default(self):
        netsim = SimNetPlugin()
        self.assertEqual([], netsim._args.upload)
        self.assertEqual([], netsim._args.download)
        self.assertEqual('lo', netsim._args.interface)
        self.assertIsNone(netsim._args.ifbdevice)
        self.assertFalse(netsim._args.clear)
        self.assertFalse(netsim._args.verbose)
        self.assertFalse(netsim._args.clearonly_mode)

    def test_configure(self):
        netsim = SimNetPlugin()
        netsim.configure(clear=True, verbose=True, interface='eth0', ifbdevice='ifb0')
        self.assertEqual([], netsim._args.upload)
        self.assertEqual([], netsim._args.download)
        self.assertEqual('eth0', netsim._args.interface)
        self.assertEqual('ifb0', netsim._args.ifbdevice)
        self.assertTrue(netsim._args.clear)
        self.assertTrue(netsim._args.verbose)
        self.assertFalse(netsim._args.clearonly_mode)

    def test_setup(self):
        netsim = SimNetPlugin()
        netsim.setup(upload=True, protocol="tcp", porttype="dport",  range="5000", rate="512kbit")
        self.assertEqual(['tcp:dport:5000:512kbit'], netsim._args.upload)
        self.assertEqual([], netsim._args.download)

    def test_setup_complex(self):
        netsim = SimNetPlugin()
        netsim.setup(upload=True, protocol="tcp", porttype="dport",  range="5000", rate="512kbit")
        netsim.setup(upload=True, protocol="udp", range="all", rate="1mbit", jitter="5%")
        netsim.setup(download=True, protocol="tcp", porttype="sport", range="8000-8080", jitter="10%")
        self.assertEqual(['tcp:dport:5000:512kbit', 'udp:all:1mbit:5%'], netsim._args.upload)
        self.assertEqual(['tcp:sport:8000-8080:10%'], netsim._args.download)

    def test_setup_assertion(self):
        netsim = SimNetPlugin()
        self.assertRaises(AssertionError, netsim.setup, upload=True, download=True)
        self.assertRaises(AssertionError, netsim.setup, upload=False, download=False)


if __name__ == '__main__':
    unittest.main()
