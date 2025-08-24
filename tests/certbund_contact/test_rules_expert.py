# -*- coding: utf-8 -*-

"""
Testing certbund_contact rules expert
"""

from copy import deepcopy
from tempfile import TemporaryDirectory

import unittest

import intelmq.lib.test as test
from intelmq_certbund_contact.bots.experts.certbund_rules.expert import CERTBundRuleExpertBot


DELETE_EXAMPLE_INPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {},
    }

DELETE_EXAMPLE_OUTPUT = {
    "__type": "Event",
    "comment": "foobar",
    }

NO_DELETE_EXAMPLE_INPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {"foo": "bar"},
    }

NO_DELETE_EXAMPLE_OUTPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {"foo": "bar"},
    }


class TestCERTBundRuleExpertBot(test.BotTestCase, unittest.TestCase):
    """
    A TestCase for CERTBundRuleExpertBot.
    """

    @classmethod
    def set_bot(cls):
        cls.bot_reference = CERTBundRuleExpertBot
        cls.temp_rules_dir = TemporaryDirectory()
        cls.sysconfig = {'script_directory': cls.temp_rules_dir.name}
        cls.default_input_message = DELETE_EXAMPLE_INPUT
        cls.allowed_warning_count = 1

    @classmethod
    def tearDownClass(cls):
        cls.temp_rules_dir.cleanup()

    def test_delete(self):
        self.input_message = DELETE_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, DELETE_EXAMPLE_OUTPUT)

    def test_no_delete(self):
        self.input_message = NO_DELETE_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, NO_DELETE_EXAMPLE_OUTPUT)


if __name__ == "__main__":
    unittest.main()
