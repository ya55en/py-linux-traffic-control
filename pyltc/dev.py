"""
Linux sockios.h is here:
  http://lxr.free-electrons.com/source/include/uapi/linux/sockios.h

"""


from os.path import join as pjoin
import socket
import fcntl
import struct


class NetDevice(object):

    @classmethod
    def all_iface_names(cls, filter=None):
        # /sys/class/net/
        return ['lo', 'eth0']

    def get_ip_word(self, ifname, offset):
        ifname = bytes(ifname, 'ascii')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            info = fcntl.ioctl(s.fileno(), offset, struct.pack('256s', ifname[:15]))
        return socket.inet_ntoa(info[20:24])

    def ip_address(self, ifname):
        return self.get_ip_word(ifname, 0x8915)

    def ip_netmask(self, ifname):
        return self.get_ip_word(ifname, 0x891b)

    def hw_address(self, ifname):
        # fname = pjoin(os.sep, "sys", "class", "net", ifname, "address")  # "/sys/class/net/{}/address".format(ifname.decode('ascii'))
        # with open(fname) as fhl:
        #     return fhl.read().strip()
        ifname = bytes(ifname, 'ascii')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        hwaddr = ':'.join(('%02x' % char for char in info[18:24]))
        return hwaddr

    def config(self, ip, netmask=None):
        pass

    def exists(self):
        return False

    def is_up(self):
        # /sys/class/net/{name}/operstate
        return False

    def create(self):
        # ip link add dummy0 type dummy
        pass

    def up(self):
        # ip link set dev dummy0 up
        pass

    def down(self):
        # ip link set dev dummy0 down
        pass


class IfbDevice(NetDevice):

    @classmethod
    def ensure_ifb_module(cls):
        pass

    @classmethod
    def get_ifb(cls, name=None):
        pass


"""
Testing:


for iface in all_('dummy'): iface.down()
`sudo modprobe --remove dummy`

`sudo modprobe dummy numdummies=0`

dev = NetDevice('dummy0')
dev.ceate()
exists()
is_up() -> False

dev.ip()
is_up() -> True

for iface in all_('dummy'): iface.down()
`sudo modprobe --remove dummy`


"""


import unittest

class TestNetDevice(unittest.TestCase):

    def test_get_ip_addrr(self):
        print(get_ip_address('lo'), get_ip_netmask('lo'))
        print(get_ip_address('enp0s3'), get_ip_netmask('enp0s3'))

    def test_get_hw_addrr(self):
        print(get_hw_address('lo'))
        print(get_hw_address('enp0s3'))


    def wishful_api(self):
        dev = NetDevice('ifb?')
        dev.map_to_existing()
        dev = NetDevice('eth0')
        dev.exists()
        dev.setup(ipaddr='95.87.121.43')
        dev.setup()
