

import collections

def issequenceforme(obj):
    if isinstance(obj, (str, bytes)):
        return False
    if isinstance(obj, set):
        return True
    return isinstance(obj, collections.Sequence)


import unittest

class TestFunctions(unittest.TestCase):

    def test_issequenceforme_true(self):
        self.assertTrue(issequenceforme(list()))
        self.assertTrue(issequenceforme(tuple()))
        self.assertTrue(issequenceforme(set()))
        self.assertTrue(issequenceforme(range(10)))

    def test_issequenceforme_false(self):
        self.assertFalse(issequenceforme(42))
        self.assertFalse(issequenceforme(dict()))


if __name__ == '__main__':
    unittest.main()
