
import unittest

from pyltc.util.rates import convert2bps, split_rate


class TestRate2Bps(unittest.TestCase):

    def test_bits_bytes(self):
        self.assertEqual(5, convert2bps('5bit'))
        self.assertEqual(32, convert2bps('4bps'))

    def test_kilo(self):
        self.assertEqual(1000, convert2bps('1kbit'))
        self.assertEqual(1024, convert2bps('1kibit'))
        self.assertEqual(8000, convert2bps('1kbps'))
        self.assertEqual(8192, convert2bps('1kibps'))

    def test_mega(self):
        self.assertEqual(1000000, convert2bps('1mbit'))
        self.assertEqual(1048576, convert2bps('1mibit'))
        self.assertEqual(8000000, convert2bps('1mbps'))
        self.assertEqual(8388608, convert2bps('1mibps'))

    def test_giga(self):
        self.assertEqual(1000000000, convert2bps('1gbit'))
        self.assertEqual(1073741824, convert2bps('1gibit'))
        self.assertEqual(8000000000, convert2bps('1gbps'))
        self.assertEqual(8589934592, convert2bps('1gibps'))

    def test_tera(self):
        self.assertEqual(1000000000000, convert2bps('1tbit'))
        self.assertEqual(1099511627776, convert2bps('1tibit'))
        self.assertEqual(8000000000000, convert2bps('1tbps'))
        self.assertEqual(8796093022208, convert2bps('1tibps'))


class TestValidateRate(unittest.TestCase):

    def test_non_alphanum(self):
        self.assertRaises(ValueError, split_rate, '5kbit!', validate=True)
        self.assertRaises(ValueError, split_rate, '5 kbit!', validate=True)

    def test_wrong_order(self):
        self.assertRaises(ValueError, split_rate, 'kbit5', validate=True)
        self.assertRaises(ValueError, split_rate, 'kbit 5', validate=True)

    def test_wrong_suffix(self):
        self.assertRaises(ValueError, split_rate, '5kbuts', validate=True)
        self.assertRaises(ValueError, split_rate, '5foos', validate=True)

    def test_wrong_suffix_passes(self):
        self.assertEqual((5, 'kbuts'), split_rate('5kbuts', validate=False))
        self.assertEqual((5, 'foos'), split_rate('5foos', validate=False))


class TestSplitRate(unittest.TestCase):

    def test_bit(self):
        self.assertEqual((512, 'bit'), split_rate('512bit'))
        self.assertEqual((54, 'bit'), split_rate('54bit'))
        self.assertEqual((4, 'bit'), split_rate('4bit'))

    def test_kbit(self):
        self.assertEqual((512, 'kbit'), split_rate('512kbit'))
        self.assertEqual((54, 'kbit'), split_rate('54kbit'))
        self.assertEqual((4, 'kbit'), split_rate('4kbit'))
        self.assertRaises(ValueError, split_rate, 'kbit')

    def test_kibit(self):
        self.assertEqual((512, 'kibit'), split_rate('512kibit'))
        self.assertEqual((54, 'kibit'), split_rate('54kibit'))
        self.assertEqual((4, 'kibit'), split_rate('4kibit'))
        self.assertRaises(ValueError, split_rate, 'kibit')

    def test_bps(self):
        self.assertEqual((512, 'bps'), split_rate('512bps'))
        self.assertEqual((54, 'bps'), split_rate('54bps'))
        self.assertEqual((4, 'bps'), split_rate('4bps'))

    def test_kbps(self):
        self.assertEqual((512, 'kbps'), split_rate('512kbps'))
        self.assertEqual((54, 'kbps'), split_rate('54kbps'))
        self.assertEqual((4, 'kbps'), split_rate('4kbps'))
        self.assertRaises(ValueError, split_rate, 'kbps')

    def test_kibps(self):
        self.assertEqual((512, 'kibps'), split_rate('512kibps'))
        self.assertEqual((54, 'kibps'), split_rate('54kibps'))
        self.assertEqual((4, 'kibps'), split_rate('4kibps'))
        self.assertRaises(ValueError, split_rate, 'kibps')


if __name__ == '__main__':
    unittest.main()
