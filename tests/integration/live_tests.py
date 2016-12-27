"""
Live tests for pyltc.

We execute actual tc commands and then launch iperf server and client
and measure the badwith.

"""
from os.path import abspath, normpath, dirname, join as pjoin
REPO_ROOT = normpath(abspath(pjoin(dirname(__file__), "..", "..")))

import sys
if not REPO_ROOT in sys.path:
    sys.path.append(REPO_ROOT)

import unittest
from pyltc import DIR_EGRESS
from pyltc.main import pyltc_entry_point
from pyltc.plugins.util import parse_branch
from pyltc.util.rates import convert2bps
from tests.util.base import LtcLiveTargetRun
from tests.util.iperf_proc import TCPNetPerfTest
from pyltc.target import TcTarget


#: the standard duration for which the iperf client sends data to the iperf server
DURATION = 2
#: shall the test runs be verbose or not (TODO: make this a command line option)
VERBOSITY = False
#: the ratio of measured/expected rate when no shaping is applied that we tolerate as acceptable for tests to pass
MAX_FREE_RATE_TOLERANCE = 0.75
MAX_SHAPED_TOLERANCE = 0.25
RECORD_MODE = True


class TcRecordTarget(TcTarget):

    """A Target class that sends generated commands to caller
    instead of executing/writing in file. Used for testing purposes."""

    def __init__(self, iface, arg_list, direction=DIR_EGRESS):
        TcTarget.__init__(self, iface, direction=direction)

    def configure(self, *args, **kw):
        pass

    def install(self, verbose=False):
        pass


class TestPyLtcLive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if RECORD_MODE:
            print('RECORD MODE')
            cls._record_count = 0
        else:
            pyltc_entry_point(['tc', '-i', 'lo', '-c', '-in'])
            pyltc_entry_point(['tc', '-i', 'lo', '-c', '--dclass', 'tcp:15000:512kbit', '--dclass', 'tcp:16001-16005:1mbit'])
            tcp_netperf = TCPNetPerfTest('dummy', ip='127.0.0.1', port=5001, duration=2)
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

    def _do_live(self, cases, tcp_free_rate=None, udp_free_rate=None):
        if not tcp_free_rate:
            tcp_free_rate = self.tcp_free_rate
        assert tcp_free_rate or udp_free_rate

        arg_list = ['tc', '-i', 'lo', '-c']
        for case in cases:
            arg_list.extend(('--dclass', case))

        if VERBOSITY:
            arg_list.append('-v')
        live_test = LtcLiveTargetRun(arg_list, udp_sendrate='10mbit', duration=DURATION)
        live_test.run()
        for case in cases:
            assert ('tcp' in case and tcp_free_rate) or ('udp' in case and udp_free_rate),\
                    'case: {!r}, tcp_free_rate: {!r}, udp_free_rate: {!r}'.format(case, tcp_free_rate, udp_free_rate)
            free_rate = tcp_free_rate if 'tcp' in case else udp_free_rate
            branch = parse_branch(case)
            results = live_test.result[case]
            self._check_bandwidth(convert2bps(branch['rate']), results['left_in'], MAX_SHAPED_TOLERANCE)
            self._check_bandwidth(free_rate, results['left_out'], MAX_FREE_RATE_TOLERANCE)
            self._check_bandwidth(convert2bps(branch['rate']), results['right_in'], MAX_SHAPED_TOLERANCE)
            self._check_bandwidth(free_rate, results['right_out'], MAX_FREE_RATE_TOLERANCE)


    def _target_factory(self, iface, direction):
        target = TcRecordTarget(iface, direction)
        self._targets.append(target)
#         print("_target_factory() produced", target)
        return target

    def _create_data_file(self, arg_list, targets):
        self.__class__._record_count += 1
        fname = pjoin(REPO_ROOT, 'tests/integration/data/testfile{}'.format(self._record_count))
        with open(fname, 'w') as fhl:
#         with open('./data/tesfile{}'.format(self._record_count), 'w') as fhl:
            fhl.write(" ".join(arg_list) + '\n\n')
            assert len(targets) == 2 and (bool(targets[0]._commands) != bool(targets[1]._commands)), "targets: {}".format(targets)
            target = targets[0] if targets[0] else targets[1]
            for line in target._commands:
                fhl.write(line + '\n')

    def _do_test(self, cases, tcp_free_rate=None, udp_free_rate=None):
        if RECORD_MODE:
            arg_list = ['tc', '-i', 'lo', '-c']
            for case in cases:
                arg_list.extend(('--dclass', case))
            pyltc_entry_point(arg_list, self._target_factory)
            self._create_data_file(arg_list, self._targets)
        else:
            self._do_live(cases, tcp_free_rate=None, udp_free_rate=None)

    def test_simple_tcp(self):
        print('test_simple_tcp BEGIN')
        cases = ['tcp:9100-9110:512kbit']
        self._do_test(cases)
        print('test_simple_tcp END')

    def test_single_port_tcp(self):
        print('test_single_port_tcp BEGIN')
        cases = ['tcp:9200:3mbit']
        self._do_test(cases)
        print('test_single_port_tcp END')

    def test_double_tcp(self):
        print('test_double_tcp BEGIN')
        cases = ['tcp:9300:1mbit', 'tcp:9400-9410:512kbit']
        self._do_test(cases)
        print('test_double_tcp END')

    def test_simple_udp(self):
        print('test_simple_udp BEGIN')
        cases = ['udp:9500-9510:2mbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_simple_udp END')

    def test_single_port_udp(self):
        print('test_single_port_udp BEGIN')
        cases = ['udp:9600:256kbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_single_port_udp END')

    def test_double_udp(self):
        print('test_double_udp BEGIN')
        cases = ['udp:9700:4mbit', 'udp:9800-9810:2mbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_double_udp END')

    def test_ingress_tcp(self):
        print('test_ingress_simple BEGIN')
        cases = ['tcp:9900-9910:1mbit']
        self._do_test(cases)
        print('test_ingress_simple END')

    def test_ingress_udp(self):
        print('test_ingress_simple BEGIN')
        cases = ['udp:10000-10010:2mbit']
        self._do_test(cases, udp_free_rate=10000000)
        print('test_ingress_simple END')

    def test_ingress_complex(self):
        print('test_ingress_complex BEGIN')
        cases = ['tcp:10100:786kbit', 'udp:10200-10210:3mbit']
        self._do_test(cases, udp_free_rate=10000000)

        print('test_ingress_complex END')


if __name__ == '__main__':
    unittest.main()
