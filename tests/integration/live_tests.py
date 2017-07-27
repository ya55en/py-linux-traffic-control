"""
Live tests for pyltc.

We execute actual tc commands and then launch ``iperf`` server and client
and measure the bandwidth.

"""
import unittest
import os
import sys
import shutil
from os.path import abspath, normpath, dirname, exists, join as pjoin


REPO_ROOT = normpath(abspath(pjoin(dirname(__file__), "..", "..")))
if not REPO_ROOT in sys.path:
    sys.path.append(REPO_ROOT)

from pyltc.core import DIR_EGRESS
from pyltc.main import pyltc_entry_point
from pyltc.plugins.simnet.util import BranchParser
from pyltc.util.rates import convert2bps
from pyltc.util.counter import Counter
from tests.util.base import LtcLiveTargetRun
from tests.util.iperf_proc import TCPNetPerfTest
from pyltc.core.target import TcTarget


#: the standard duration (in sec.) for which the iperf client sends data to the iperf server
DURATION = 2
#: shall the test runs be verbose or not (TODO: make this a command line option)
VERBOSITY = False
#: the ratio of measured/expected rate when no shaping is applied that we tolerate as acceptable for tests to pass
MAX_FREE_RATE_TOLERANCE = 0.75
MAX_SHAPED_TOLERANCE = 0.25

DEFAULT_TEST_HOST = '127.0.0.1'
DEFAULT_TEST_PORT = 5001


class TcRecordTarget(TcTarget):
    """A Target class that sends generated commands to caller
    instead of executing/writing in file. Used for testing purposes."""

    def __init__(self, iface, arg_list, direction=DIR_EGRESS):
        TcTarget.__init__(self, iface, direction=direction)

    def configure(self, *args, **kw):
        pass

    def marshal(self, verbose=False):
        pass


class TestPyLtcLive(unittest.TestCase):
    """
    Live test setting up traffic control and then executing iperf server + client
    for different ports (shaped and not-shaped).
    """

    record_mode = False

    @classmethod
    def setUpClass(cls):
        if cls.record_mode:
            print('--Record mode ON--')
            cls._rec_count = Counter(start=1)
            data_dir = pjoin(REPO_ROOT, "tmp", "testdata", "recorded")
            if exists(data_dir):
                shutil.rmtree(data_dir)
            assert not exists(data_dir)
            os.makedirs(data_dir)
            cls._data_dir = data_dir

        else:
            print('--Record mode OFF--')
            pyltc_entry_point(['simnet', '-i', 'lo', '-c', '-b'])
            pyltc_entry_point(['simnet', '-i', 'lo', '-c', '--upload', 'tcp:dport:15000:512kbit', 'tcp:dport:16001-16005:1mbit'])
            tcp_netperf = TCPNetPerfTest('dummy', host='127.0.0.1', port=DEFAULT_TEST_PORT, duration=DURATION)
            cls.tcp_free_rate = tcp_netperf.run()

    def setUp(self):
        self._targets = list()

    def _err_message(self, margin, actual):
        return 'Expected relative error margin max {} but got {}'.format(margin, actual)

    def _check_bandwidth(self, norm, bandwidth, margin):
        if bandwidth > norm:
            actual = bandwidth / norm - 1.0
            print('norm: {!r}, bandwidth: {!r}, margin: {!r}, actual: {:.4f}'.format(norm, bandwidth, margin, actual))
            self.assertLess(actual, margin, self._err_message(margin, actual))
        elif bandwidth < norm:
            actual = norm / bandwidth - 1.0
            print('norm: {!r}, bandwidth: {!r}, margin: {!r}, actual: {:.4f}'.format(norm, bandwidth, margin, actual))
            self.assertLess(actual, margin, self._err_message(margin, actual))
        else:
            self.assertEqual(norm, bandwidth)

    def tc_recording_target_factory(self, iface, direction):
        target = TcRecordTarget(iface, direction)
        self._targets.append(target)
        return target

    def _do_live(self, cases, tcp_free_rate=None, udp_free_rate=None):
        if not tcp_free_rate:
            tcp_free_rate = self.tcp_free_rate
        assert tcp_free_rate or udp_free_rate

        arg_list = ['simnet', '-i', 'lo', '-c']
        arg_list.append('--upload')
        for case in cases:
            arg_list.append(case)

        if VERBOSITY:
            arg_list.append('-v')
        live_test = LtcLiveTargetRun(arg_list, udp_sendrate='10mbit', duration=DURATION)
        live_test.run()
        for case in cases:
            assert ('tcp' in case and tcp_free_rate) or ('udp' in case and udp_free_rate), \
                    'case: {!r}, tcp_free_rate: {!r}, udp_free_rate: {!r}'.format(case, tcp_free_rate, udp_free_rate)
            free_rate = tcp_free_rate if 'tcp' in case else udp_free_rate
            print('case: {}, free_rate: {}'.format(case, free_rate))
            branch = BranchParser(case, upload=True).as_dict()
            results = live_test.result[case]
            self._check_bandwidth(convert2bps(branch['rate']), results['left_in'], MAX_SHAPED_TOLERANCE)
            self._check_bandwidth(free_rate, results['left_out'], MAX_FREE_RATE_TOLERANCE)
            self._check_bandwidth(convert2bps(branch['rate']), results['right_in'], MAX_SHAPED_TOLERANCE)
            self._check_bandwidth(free_rate, results['right_out'], MAX_FREE_RATE_TOLERANCE)

    def _do_record(self, cases):
        arg_list = ['simnet', '-i', 'lo', '-c']
        arg_list.append('--upload')
        for case in cases:
            arg_list.append(case)
        pyltc_entry_point(arg_list, self.tc_recording_target_factory)
        self._create_data_file(arg_list, self._targets)

    def _create_data_file(self, arg_list, targets):
        #print(self._data_dir)
        fname = pjoin(self._data_dir, "testfile-{}.txt".format(self._rec_count.next()))
        with open(fname, 'w') as fhl:
            fhl.write(" ".join(arg_list) + '\n\n')
            assert len(targets) == 2 and (bool(targets[0]._commands) != bool(targets[1]._commands)), "targets: {}".format(targets)
            target = targets[0] if targets[0] else targets[1]
            for line in target._commands:
                fhl.write(line + '\n')

    def _do_test(self, cases, tcp_free_rate=None, udp_free_rate=None):
        if self.record_mode:
            self._do_record(cases)
        else:
            self._do_live(cases, tcp_free_rate, udp_free_rate)

    def test_simple_tcp(self):
        print('test_simple_tcp BEGIN')
        cases = ['tcp:dport:9100-9110:512kbit']
        self._do_test(cases)
        print('test_simple_tcp END')

    def test_single_port_tcp(self):
        print('test_single_port_tcp BEGIN')
        cases = ['tcp:dport:9200:3mbit']
        self._do_test(cases)
        print('test_single_port_tcp END')

    def test_double_tcp(self):
        print('test_double_tcp BEGIN')
        cases = ['tcp:dport:9300:1mbit', 'tcp:dport:9400-9410:512kbit']
        self._do_test(cases)
        print('test_double_tcp END')

    def test_simple_udp(self):
        print('test_simple_udp BEGIN')
        cases = ['udp:dport:9500-9510:2mbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_simple_udp END')

    def test_single_port_udp(self):
        print('test_single_port_udp BEGIN')
        cases = ['udp:dport:9600:256kbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_single_port_udp END')

    def test_double_udp(self):
        print('test_double_udp BEGIN')
        cases = ['udp:dport:9700:4mbit', 'udp:dport:9800-9810:2mbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_double_udp END')

    def test_ingress_tcp(self):
        print('test_ingress_simple BEGIN')
        cases = ['tcp:dport:9900-9910:1mbit']
        self._do_test(cases)
        print('test_ingress_simple END')

#     def _test_ingress_udp(self):
#         print('test_ingress_simple BEGIN')
#         cases = ['udp:dport:10000-10010:2mbit']
#         self._do_test(cases, udp_free_rate=10000000)
#         print('test_ingress_simple END')

    def test_complex(self):
        print('test_ingress_complex BEGIN')
        cases = ['tcp:dport:10100:786kbit', 'udp:dport:10200-10210:3mbit']
        self._do_test(cases, udp_free_rate=10000000)

        print('test_ingress_complex END')


if __name__ == '__main__':
    import sys
    if 'record' in sys.argv:
        TestPyLtcLive.record_mode = True
        sys.argv.remove('record')
        print('Record mode detected')
    unittest.main()
