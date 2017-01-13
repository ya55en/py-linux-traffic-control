"""
Unit tests for the pyltc.core.netdevice module.

"""
import unittest
from unittest import mock
from unittest.mock import call

from pyltc.core.netdevice import DeviceManager, NetDevice


class MockedModuleTest(unittest.TestCase):
    """Tests DeviceManager and NetDevice without actually creating or removing
    devices. Can be run w/o root access level."""

    def test_split_name(self):
        self.assertEqual(('dummy', 0), DeviceManager.split_name('dummy0'))
        self.assertEqual(('ifb', 883), DeviceManager.split_name('ifb883'))
        self.assertEqual(('dummy', None), DeviceManager.split_name('dummy'))

    @mock.patch('pyltc.core.netdevice.os.listdir')
    def test_minimal_nonexisting_name_case1(self, fake_listdir):
        fake_listdir.return_value = ['eth0']
        new_name = NetDevice.minimal_nonexisting_name('dummy')
        self.assertEqual('dummy0', new_name)
        self.assertEqual(1, fake_listdir.call_count)

    @mock.patch('pyltc.core.netdevice.os.listdir')
    def test_minimal_nonexisting_name_case2(self, fake_listdir):
        fake_listdir.return_value = ['dummy1', 'eth0', 'dummy0']
        new_name = NetDevice.minimal_nonexisting_name('dummy')
        self.assertEqual('dummy2', new_name)
        self.assertEqual(1, fake_listdir.call_count)

    @mock.patch('pyltc.core.netdevice.DeviceManager.device_add')
    @mock.patch('pyltc.core.netdevice.DeviceManager.load_module')
    @mock.patch('pyltc.core.netdevice.os.listdir')
    def test_get_device_device_exists(self, fake_listdir, fake_load_module, fake_device_add):
        fake_listdir.return_value = ['ifb0', 'eth0']
        dev = NetDevice.get_device('ifb0')
        self.assertEqual('ifb0', dev.name)
        self.assertEqual(1, fake_listdir.call_count)
        fake_load_module.assert_not_called()
        fake_device_add.assert_not_called()

    @mock.patch('pyltc.core.netdevice.DeviceManager.device_add')
    @mock.patch('pyltc.core.netdevice.DeviceManager.load_module')
    @mock.patch('pyltc.core.netdevice.os.listdir')
    def test_get_device_no_such_devices(self, fake_listdir, fake_load_module, fake_device_add):
        fake_listdir.return_value = ['eth0']
        dev = NetDevice.get_device('ifb')
        self.assertEqual('ifb0', dev.name)
        self.assertEqual(2, fake_listdir.call_count)
        fake_load_module.assert_called_once_with('ifb')
        fake_device_add.assert_called_once_with('ifb0')

    @mock.patch('pyltc.core.netdevice.DeviceManager.device_add')
    @mock.patch('pyltc.core.netdevice.DeviceManager.load_module')
    @mock.patch('pyltc.core.netdevice.DeviceManager.all_iface_names')
    def test_get_device_two_such_devices(self, fake_all_iface_names, fake_load_module, fake_device_add):
        fake_all_iface_names.return_value = ['ifb0', 'eth0', 'ifb1']
        dev = NetDevice.get_device('ifb')
        self.assertEqual('ifb2', dev.name)
        fake_all_iface_names.assert_has_calls([call(), call('ifb')])
        fake_load_module.assert_called_once_with('ifb')
        fake_device_add.assert_called_once_with('ifb2')


class LiveModuleTest(unittest.TestCase):
    """Tests DeviceManager and NetDevice with loading module(s) and creating, reconfiguring
    and removing devices. Can be run only WITH root access level."""

    @classmethod
    def setUpClass(cls):
        DeviceManager.shutdown_module('dummy')
        all_dummies = DeviceManager.all_iface_names(filter='dummy')
        assert [] == all_dummies, "not empty: {!r}".format(all_dummies)
        DeviceManager.load_module('dummy', numdummies=0)

    @classmethod
    def tearDownClass(cls):
        DeviceManager.shutdown_module('dummy')

    def test_typical_scenario(self):
        dev = NetDevice('dummy0')
        self.assertFalse(dev.exists())
        dev.add()
        self.assertTrue(dev.exists())
        self.assertFalse(dev.is_up())
        self.assertTrue(dev.is_down())
        dev.up()
        self.assertTrue(dev.is_up())
        dev.down()
        self.assertTrue(dev.is_down())


# FIXME: write tests for IfbDevice
# class TestIfbDevice(unittest.TestCase):
#
#     def wishful_api_2(self):
#         dev = DeviceManager('dummy1')
#         ifbdev = IfbDevice.get_device()
#         dev.set_ingress_ifb(ifbdev)
#         dev.egress.set_root_qdisc('htb')
#         dev.ingress.set_root_qdisc('htb')