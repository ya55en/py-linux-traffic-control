"""
Unit tests for the util.counter module.

"""
import unittest

from pyltc.util.counter import Counter


class TestCounter(unittest.TestCase):

    def test_creation_default(self):
        cnt = Counter()
        self.assertEqual(0, cnt._start)
        self.assertEqual(1, cnt._incr)
        self.assertIsNone(cnt._fmt)
        self.assertEqual(set(), cnt._skip)

    def test_creation_set_start(self):
        cnt = Counter(start=10)
        self.assertEqual(10, cnt._start)

    def test_creation_set_incr(self):
        cnt = Counter(incr=2)
        self.assertEqual(2, cnt._incr)

    def test_creation_set_fmt(self):
        cnt = Counter(fmt='0x{:012x}')
        self.assertEqual('0x{:012x}', cnt._fmt)

    def test_creation_set_skip(self):
        cnt = Counter(skip=range(3, 6))
        self.assertEqual({3, 4, 5}, cnt._skip)

    def test_creation_set_end(self):
        cnt = Counter(end=5)
        self.assertEqual(5, cnt._end)

    def test_skip_scalar(self):
        cnt = Counter(skip=range(2, 4))
        self.assertEqual({2, 3}, cnt._skip)
        cnt.skip(9)
        self.assertEqual({2, 3, 9}, cnt._skip)

    def test_skip_sequence(self):
        cnt = Counter(skip=range(12, 16))
        self.assertEqual({12, 13, 14, 15}, cnt._skip)
        cnt.skip(range(22, 24))
        self.assertEqual({12, 13, 14, 15, 22, 23}, cnt._skip)

    def test__isproperskipsequence_true(self):
        self.assertTrue(Counter._isproperskipsequence(list()))
        self.assertTrue(Counter._isproperskipsequence(tuple()))
        self.assertTrue(Counter._isproperskipsequence(set()))
        self.assertTrue(Counter._isproperskipsequence(range(10, 12)))

    def test__isproperskipsequence_false(self):
        self.assertFalse(Counter._isproperskipsequence(42))
        self.assertFalse(Counter._isproperskipsequence(3.14159))
        self.assertFalse(Counter._isproperskipsequence(dict()))

    def test_skip_sequence_wrong_arg_raises_type_error(self):
        cnt = Counter(skip=range(10, 12))
        self.assertRaisesRegex(TypeError, "Expected int or sequence but got", cnt.skip, b'some bytes')
        self.assertRaisesRegex(TypeError, "Expected int or sequence but got", cnt.skip, 'some string')
        self.assertRaisesRegex(TypeError, "Expected int or sequence but got", cnt.skip, 3.1416)

    def test_next_endless(self):
        cnt = Counter()
        for expected in range(1000):
            self.assertEqual(expected, next(cnt))

    def test_next_with_end(self):
        cnt = Counter(end=4)
        self.assertEqual(0, cnt.next())
        self.assertEqual(1, cnt.next())
        self.assertEqual(2, cnt.next())
        self.assertEqual(3, cnt.next())
        self.assertRaises(StopIteration, cnt.next)

    def test_next_complex(self):
        cnt = Counter(start=2, incr=2, skip={3, 4, 5})  # fmt='int({})'
        cnt.skip(7)
        cnt.skip({8, 9})
        self.assertEqual(2, cnt.next())
        self.assertEqual(6, cnt.next())
        self.assertEqual(10, cnt.next())
        self.assertEqual(12, cnt.next())
        self.assertEqual(14, cnt.next())
        self.assertEqual(16, cnt.next())

    def test_next_with_fmt(self):
        cnt = Counter(start=-2, incr=-2, skip=-6, fmt='int({:d})')
        cnt.skip(-7)
        cnt.skip(-12)
        self.assertEqual('int(-2)', cnt.next())
        self.assertEqual('int(-4)', cnt.next())
        self.assertEqual('int(-8)', cnt.next())
        self.assertEqual('int(-10)', cnt.next())
        self.assertEqual('int(-14)', cnt.next())
        self.assertEqual('int(-16)', cnt.next())
        self.assertEqual('int(-18)', cnt.next())

    def test_iteration(self):
        cnt = Counter(end=10)
        for expected, count in enumerate(cnt):
            self.assertEqual(expected, count)

    def test_value(self):
        cnt = Counter()
        self.assertEqual(0, cnt.next())
        self.assertEqual(1, cnt.next())
        self.assertEqual(2, cnt.next())
        self.assertEqual(2, cnt.value())
        self.assertEqual(2, cnt.value())
        self.assertEqual(3, cnt.next())
        self.assertEqual(3, cnt.value())
        self.assertEqual(3, cnt.value())

    def wishful_api(self):
        c = Counter(start=99, incr=-1, fmt='0x{:0x}')
        c.next()
        c.skip(5)
        c.skip(range(9, 11))
        c.next()
        c.next()
        c.next()
        c.reset()


if __name__ == '__main__':
    unittest.main()
