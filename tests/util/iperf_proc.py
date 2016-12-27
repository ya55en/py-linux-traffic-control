"""
Iperf network performance testing module.
Used by tests for simple bandwidth measurements; uses iperf.

"""

import time

from pyltc.util.cmdline import CommandLine


# FIXME: Do we need these? Remove if not.
OUTPUT_REGEXP = r'^\[.*?\]\s+\d+\.\d+\-\d+\.\d+\s+sec\s+\d[\.\d]+\s+\w+\s+(\d+)\s+bits/sec.*$'
TIMEOUT = 60


class Iperf3Server(object):
    """Used for running iperf server component
    iperf3 -s 127.0.0.1 -p 5005 -1 -i 0 -f b
    iperf -[u]s -B 127.0.0.1 -p 9003 -f b"""

    def __init__(self, iperf_bin='iperf', ip='127.0.0.1', port=5001):
        self._iperf_bin = iperf_bin
        self._ip = ip
        self._port = port
        self.cmd = None
        self.thread = None

    def run(self, protocol):
        cmd_tmpl = "{} -s -B {} -p {} -f b -y C" if protocol == 'tcp' else "{} -us -B {} -p {} -f b -y C"
        cmd_text = cmd_tmpl.format(self._iperf_bin, self._ip, self._port)
        print('cmd_text(server): {!r}'.format(cmd_text))
        self.cmd = CommandLine(cmd_text)
        self.cmd.execute_daemon()
        return self.cmd

    def join(self): # TODO: Perhaps not used anymore?
        self.thread.join()


class Iperf3Client(object):
    """Parent of TCPClient and UDPClient"""

    def __init__(self, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        self._iperf_bin = iperf_bin
        self._ip = ip
        self._port = port
        self._duration = duration


class TCPClient(Iperf3Client):
    """Used for running iperf client component in TCP mode.
    iperf3 -s 127.0.0.1 -p 5005 -1 -i 0 -f b
    iperf -[u]s -B 127.0.0.1 -p 9003 -f b"""

    def __init__(self, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        super(TCPClient, self).__init__(iperf_bin=iperf_bin, ip=ip, port=port, duration=duration)

    def run(self):
        cmd_text = "{} -c {} -p {} -t {} -f b".format(self._iperf_bin, self._ip, self._port, self._duration)
        print('cmd_text(tcpclient): {!r}'.format(cmd_text))
        self.cmd = CommandLine(cmd_text).execute_daemon()
        return self.cmd


class UDPClient(Iperf3Client):
    """Used for running iperf client component in TCP mode.
    iperf3 -s 127.0.0.1 -p 5005 -1 -i 0 -f b
    iperf -[u]s -B 127.0.0.1 -p 9003 -f b"""

    def __init__(self, sendrate, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        super(UDPClient, self).__init__(iperf_bin=iperf_bin, ip=ip, port=port, duration=duration)
        self._sendrate = sendrate

    def run(self):
        cmd_text = "{} -uc {} -p {} -t {} -f b -b {}".format(self._iperf_bin, self._ip, self._port, self._duration, self._sendrate)
        print('cmd_text(udpclient): {!r}'.format(cmd_text))
        self.cmd = CommandLine(cmd_text).execute_daemon()
        return self.cmd


class NetPerfTest(object):
    """Parent of TCPNetPerfTest and UDPNetPerfTest,
    which wrap the iperf server-client functionallity."""

    def __init__(self, sendrate, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        self._sendrate = sendrate
        self._iperf_bin = iperf_bin
        self._ip = ip
        self._port = port
        self._duration = duration

    def _gather_server_output(self, server_cmd, client_cmd):
        output_line = None
        with server_cmd._proc.stdout:
            for line in iter(server_cmd._proc.stdout.readline, b''):
                if line:
                    output_line = line
                    rc = server_cmd.terminate()
                    if rc != None:
                        break
                    print('Unexpected None returncode after kill()!..')

        server_cmd._proc.stderr.close()
        client_cmd._proc.stdout.close()
        client_cmd._proc.stderr.close()
        assert output_line, 'No output from iperf server! cmdline: {}'.format(server_cmd.cmdline)
        return output_line

    def run(self):
        raise NotImplemented('Abstract method.')


class TCPNetPerfTest(NetPerfTest):
    """Wraps the iperf server-client functionallity for tcp."""

    def __init__(self, sendrate, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        """``sendrate`` is only a dummy argument here, to conform to NetPerfTest interface."""
        super(TCPNetPerfTest, self).__init__('dummy', iperf_bin=iperf_bin, ip=ip, port=port, duration=duration)

    def run(self):
        server = Iperf3Server(iperf_bin=self._iperf_bin, ip=self._ip, port=self._port)
        server_cmd = server.run("tcp")
        time.sleep(0.1)
        client = TCPClient(iperf_bin=self._iperf_bin, ip=self._ip, port=self._port, duration=self._duration)
        client_cmd = client.run()

        output_line = self._gather_server_output(server_cmd, client_cmd)
        return int(output_line.split(b',')[8])


class UDPNetPerfTest(NetPerfTest):
    """Wraps the iperf server-client functionallity for udp."""

    def __init__(self, sendrate, iperf_bin='iperf', ip='127.0.0.1', port=5001, duration=4):
        super(UDPNetPerfTest, self).__init__(sendrate, iperf_bin=iperf_bin, ip=ip, port=port, duration=duration)

    def run(self):
        server = Iperf3Server(iperf_bin=self._iperf_bin, ip=self._ip, port=self._port)
        server_cmd = server.run("udp")
        time.sleep(0.1)
        client = UDPClient(self._sendrate, iperf_bin=self._iperf_bin, ip=self._ip, port=self._port, duration=self._duration)
        client_cmd = client.run()

        output_line = self._gather_server_output(server_cmd, client_cmd)
        return int(output_line.split(b',')[8])


#________________________________________
#  Test Section Below:

import unittest


class ServerClientTest(unittest.TestCase):

    def test_creation(self):
        Iperf3Server(iperf_bin='iperf_bin3', ip='127.0.0.3', port=30300)
        TCPClient(iperf_bin='iperf_bin4', ip='127.0.0.4', port=40400, duration=44)
        UDPClient('10mbit', iperf_bin='iperf_bin5', ip='127.0.0.5', port=50500, duration=55)

    @unittest.skip("sould be removed/reworked")  # TODO: rework or remove
    def test_simple(self): # seems unusable at this point
        server = Iperf3Server(iperf_bin='iperf', ip='127.0.0.1', port=40400)
        server.run("tcp")
        time.sleep(0.1)
        client = TCPClient(iperf_bin='iperf', ip='127.0.0.1', port=40400, duration=4)
        client.run()
        server.join()
        bandwidth = server.get_bandwidth()
        print(bandwidth)


class TestNetPerfTest(unittest.TestCase):

    def test_creation(self):
        TCPNetPerfTest('dummy', iperf_bin='iperf_bin7', ip='127.0.0.7', port=7700, duration=77)
        UDPNetPerfTest('8mbit', iperf_bin='iperf_bin8', ip='127.0.0.8', port=8800, duration=88)

    def test_tcp(self):
        tcp_netperf = TCPNetPerfTest('dummy', ip='127.0.0.1', port=18003, duration=3)
        bandwidth = tcp_netperf.run()
        print(bandwidth)

    def test_tcp_2(self):
        tcp_netperf = TCPNetPerfTest('dummy', ip='127.0.0.1', port=8003, duration=3)
        bandwidth = tcp_netperf.run()
        print(bandwidth)

    def test_udp(self):
        udp_netperf = UDPNetPerfTest('10mbit', ip='127.0.0.1', port=17007, duration=3)
        bandwidth = udp_netperf.run()
        print(bandwidth)


if __name__ == '__main__':
    unittest.main()
