"""
Unit tests for the plug module.

"""

import unittest

from pyltc.core.plug import PluginMount


class FakePluginBaseclassOne(metaclass=PluginMount):
    __plugin_name__ = None


class FakePluginBaseclassTwo(metaclass=PluginMount):
    __plugin_name__ = None


class TestPlug(unittest.TestCase):

    def test_single_subclass(self):

        class MyFakePlugin(FakePluginBaseclassOne):
            __plugin_name__ = 'my-fake-plugin'

        self.assertEqual([MyFakePlugin], FakePluginBaseclassOne.plugins)
        self.assertEqual({'my-fake-plugin': MyFakePlugin}, FakePluginBaseclassOne.plugins_map)

    def test_duplicate_plugin_name(self):

        class MyFakePluginOne(FakePluginBaseclassTwo):
            __plugin_name__ = 'my-fake-plugin-one'

        class MyFakePluginTwo(FakePluginBaseclassTwo):
            __plugin_name__ = 'my-fake-plugin-two'

        with self.assertRaises(AssertionError):
            class MyFakePluginDuplicateOne(FakePluginBaseclassTwo):
                __plugin_name__ = 'my-fake-plugin-one'


if __name__ == '__main__':
    unittest.main()
