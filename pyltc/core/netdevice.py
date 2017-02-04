"""
Network device management classes.

"""
import os
from os.path import join as pjoin
from unittest.mock import MagicMock

from pyltc.util.cmdline import CommandLine
from pyltc.core import DIR_EGRESS, DIR_INGRESS
from pyltc.core.tfactory import default_target_factory


class DeviceManager(object):

    #: /sys/class/net/ path
    SYS_CLASS_NET = pjoin(os.sep, "sys", "class", "net")

    @classmethod
    def all_iface_names(cls, filter=None):
        result = []
        for filename in os.listdir(cls.SYS_CLASS_NET):
            if not filter or filter in filename:
                result.append(filename)
        return result

    @classmethod
    def load_module(cls, name, **kwargs):
        """Loads given module into kernel. Any kwargs are passed as key=value pairs."""
        kwargs_str = " ".join('{}={}'.format(k, v) for k, v in kwargs.items())
        cmd = 'modprobe {} {}'.format(name, kwargs_str).rstrip()
        CommandLine(cmd, sudo=True).execute()

    @classmethod
    def remove_module(cls, name):
        """Removes given module from kernel."""
        CommandLine('modprobe --remove {}'.format(name), sudo=True).execute()

    @classmethod
    def shutdown_module(cls, name):
        """Sets down all module-related devices, then removes module from kernel."""
        for ifname in cls.all_iface_names(filter=name):
            cls.device_down(ifname)
            cls.remove_module(name)

    @classmethod
    def split_name(cls, name):
        module = name.rstrip("0123456789")
        num = name[len(module):]
        return module, int(num) if num else None

    @classmethod
    def device_exists(cls, name):
        return name in cls.all_iface_names()

    @classmethod
    def device_add(cls, name):
        assert not cls.device_exists(name), 'Device already exists: {!r}'.format(name)
        module, _ = cls.split_name(name)
        CommandLine("ip link add {} type {}".format(name, module), sudo=True).execute()
        assert cls.device_exists(name)

    @classmethod
    def ensure_device(cls, name):
        if cls.device_exists(name):
            return
        cls.device_add(name)

    @classmethod
    def device_is_down(cls, name):
        """Returns True if given network device down, otherwise returns False.
        Consults /sys/class/net/{device-name}/operstate.

        :return: bool
        """
        assert cls.device_exists(name), "Device does not exist: {!r}".format(name)
        with open(pjoin(cls.SYS_CLASS_NET, name, 'operstate')) as fhl:
            return 'down' == fhl.read().strip().lower()

    @classmethod
    def device_up(cls, name):
        assert cls.device_exists(name), 'Device does NOT exist: {!r}'.format(name)
        CommandLine("ip link set dev {} up".format(name), sudo=True).execute()

    @classmethod
    def device_down(cls, name):
        assert cls.device_exists(name), 'Device does NOT exist: {!r}'.format(name)
        CommandLine("ip link set dev {} down".format(name), sudo=True).execute()


class NetDevice(object):
    """Network Device instance representation class."""

    _iface_map = None

    @classmethod
    def init(cls):
        cls._iface_map = dict()

    # TODO: how about moving this method below to DeviceManager?

    @classmethod
    def minimal_nonexisting_name(cls, module):
        """Returns the name of the network device for given module that has lowest
        sequence number.

        :param module: string - the name of the network device module (e.g. 'ifb')
        :return: string - the name of the device with lowest number (e.g. 'ifb0')
        """
        existing_names = DeviceManager.all_iface_names(module)
        if not existing_names:
            return "{}0".format(module)
        lst = sorted([DeviceManager.split_name(name) for name in existing_names], key=lambda tpl: tpl[1])
        num = lst[-1][1] + 1
        return "{}{}".format(module, num)

    @classmethod
    def get_device(cls, name_or_module, target_factory=None):
        """Returns a NetDevice instance that either wraps an existing device
        with given name. The device is added first if it does not yet exist.
        If only the module name is given (e.g. 'ifb') then the first available
        device name is picked.

        :param name_or_module: string - device name or module name
        :return: NetDevice
        """
        if name_or_module in DeviceManager.all_iface_names():
            return cls(name_or_module, target_factory)
        module, num = DeviceManager.split_name(name_or_module)
        if num is None:
            new_name = cls.minimal_nonexisting_name(module)
        else:
            new_name = "{}{}".format(module, num)
        DeviceManager.load_module(module)
        DeviceManager.device_add(new_name)
        return cls(new_name, target_factory)

    def __init__(self, name, target_factory=None):
        assert isinstance(name, str)
        self._name = name
        if not target_factory:
            target_factory = default_target_factory
        self._egress_chain = target_factory(self, DIR_EGRESS)
        self._ingress_chain = target_factory(self, DIR_INGRESS)
        self._ifbdev = None

    @classmethod
    def new_instance(cls, name, target_factory=None):
        """Creates and returns a new NetDevice instance. Ingress and egress builder chains will be
        created using given target_factory or the default one if target_factory is not provided.

        :param name: string - the name of the device as known by the kernel (e.g. 'eth0')
               If ``name`` is ``None``, a "Null object" will be returned that does
               nothing on calling any of its methods.
        :param target_factory: callable returning an ``ITarget`` - the factory to be used
               to create the Ingress and egress chain builders
        :return: NetDevice - the network device object for this device name
        """
        if name is None:
            return MagicMock()
        if target_factory is None:
            target_factory = default_target_factory
        return cls(name, target_factory)

    @classmethod
    def get_interface(cls, ifname, target_factory=None):
        try:
            return cls._iface_map[ifname]
        except KeyError:
            cls._iface_map[ifname] = iface = cls.new_instance(ifname, target_factory)
            return iface

    @property
    def name(self):
        return self._name

    @property
    def egress(self):
        return self._egress_chain

    @property
    def ingress(self):
        """Returns the ingress chain builder for this interface.
        :return: ITarget - the ingress chain target builder
        """
        return self._ingress_chain

    def exists(self):
        return DeviceManager.device_exists(self._name)

    def is_up(self):
        return not DeviceManager.device_is_down(self._name)

    def is_down(self):
        return DeviceManager.device_is_down(self._name)

    def add(self):
        DeviceManager.device_add(self._name)

    def up(self):
        DeviceManager.device_up(self._name)

    def down(self):
        DeviceManager.device_down(self._name)


class IfbDevice(NetDevice):

    @classmethod
    def load_module(cls):
        DeviceManager.load_module('ifb')

    @classmethod
    def remove_module(cls):
        DeviceManager.remove_module('ifb')

    @classmethod
    def shutdown_module(cls):
        DeviceManager.shutdown_module('ifb')

    @classmethod
    def get_device(cls, name_or_module=None):
        return NetDevice.get_device(name_or_module or 'ifb')
