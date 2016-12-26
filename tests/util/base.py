"""
Base test classes for PyLTC integration testing.

"""

from pyltc import DIR_EGRESS
from pyltc.parseargs import parse_args
from pyltc.target import TcFileTarget, TcCommandTarget
from pyltc.main import pyltc_entry_point
from tests.util.iperf_proc import TCPNetPerfTest, UDPNetPerfTest
from pyltc.plugins.util import parse_branch


class TcTestTarget(TcFileTarget):
    """A Target class that sends generated commands to caller
    instead of executing/writing in file. Used for testing purposes."""

    def __init__(self, iface, callback, direction=DIR_EGRESS):
        TcFileTarget.__init__(self, iface, direction=direction)
        self._callback = callback

    def install(self, verbose=False):
        self._callback(self._commands)


class LtcSimulateTargetRun(object):
    """Used by simulation pyltc tests.
    Executes given pyltc command using the TcTestTarget."""

    def __init__(self, argv, full=False):
        self._argv = argv
        self._full = full
        self._result = None

    def our_callback(self, result):
        self._result = result

    def test_target_factory(self, iface, direction):
        return TcTestTarget(iface, self.our_callback, direction)

    def run(self):
        pyltc_entry_point(self._argv, self.test_target_factory)

    @property
    def result(self):
        return self._result


class LtcLiveTargetRun(object):
    """Used by live pyltc tests.
    Executes given pyltc command using TcCommandTarget
    and measures rates, then returns results."""

    def __init__(self, argv, udp_sendrate, duration=5, full=False):
        self._argv = argv
        self._udp_sendrate = udp_sendrate
        self._duration = duration
        self._full = full
        self._result = None

    def _target_factory(self, iface, direction):
        return TcCommandTarget(iface, direction)

    def _test_for_port_range(self, klass, port_range, sendrate):
        left_in_port, right_in_port, *_ = map(int, (port_range + "-0").split('-'))
        right_in_port = right_in_port if right_in_port else left_in_port
        left_out_port = left_in_port - 1
        right_out_port = right_in_port + 1

        bandwidth_dict = {}
        tcp_netperf_1 = klass(sendrate, ip='127.0.0.1', port=left_in_port, duration=self._duration)
        bandwidth_dict['left_in'] = tcp_netperf_1.run()
        tcp_netperf_2 = klass(sendrate, ip='127.0.0.1', port=left_out_port, duration=self._duration)
        bandwidth_dict['left_out'] = tcp_netperf_2.run()
        tcp_netperf_3 = klass(sendrate, ip='127.0.0.1', port=right_in_port, duration=self._duration)
        bandwidth_dict['right_in'] = tcp_netperf_3.run()
        tcp_netperf_4 = klass(sendrate, ip='127.0.0.1', port=right_out_port, duration=self._duration)
        bandwidth_dict['right_out'] = tcp_netperf_4.run()

        return bandwidth_dict

    def run(self):
        orig_argv = self._argv[:]
        pyltc_entry_point(self._argv, self._target_factory)
        args = parse_args(orig_argv)
        result = {}
        for dc in args.dclass:
            dc_dict = parse_branch(dc)
            klass = TCPNetPerfTest if dc_dict['protocol'] == 'tcp' else UDPNetPerfTest
            bandwidth_dict = self._test_for_port_range(klass, dc_dict['range'], self._udp_sendrate)
            result[dc] = bandwidth_dict

        self._result = result

# This here shows an example of what the function returns (since it is not too simple):
# (as of now the 'random' ports are not yet implemented)
#         return {
#             'tcp:8080:512kbit': {
#                 'left-in': 782323,
#                 'left-out': 94839847,
#                 'right-in': 62343234234,
#                 'right-out': 82374234,
#
#                 'random-in-01': 453452345,
#                 'random-in-02': 453452345,
#                 'random-in-03': 453452345,
#                 'random-out-01': 453452345,
#                 'random-out-02': 453452345,
#                 'random-out-03': 453452345,
#             }
#         }

    @property
    def result(self):
        return self._result
