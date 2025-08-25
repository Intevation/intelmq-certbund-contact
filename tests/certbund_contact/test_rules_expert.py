# -*- coding: utf-8 -*-

"""
Testing certbund_contact rules expert
"""

from copy import deepcopy
from tempfile import TemporaryDirectory

import unittest

import intelmq.lib.test as test
from intelmq_certbund_contact.bots.experts.certbund_rules.expert import CERTBundRuleExpertBot


SOURCE_CONTACTS_EXAMPLE_INPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {
        "source_contacts": {
              "matches": [],
              "organisations": []
        }},
    }

SOURCE_CONTACTS_EXAMPLE_OUTPUT = {
    "__type": "Event",
    "comment": "foobar",
    }

EMPTY_SOURCE_DIRECTIVES_EXAMPLE_INPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {"source_directives": []},
    }

EMPTY_SOURCE_DIRECTIVES_EXAMPLE_OUTPUT = {
    "__type": "Event",
    "comment": "foobar",
    }

NON_EMPTY_CERTBUND_EXAMPLE_INPUT = {
    "__type": "Event",
    "comment": "foobar",
    "extra.certbund": {"foo": "bar"},
    }

NON_EMPTY_CERTBUND_EXAMPLE_OUTPUT = NON_EMPTY_CERTBUND_EXAMPLE_INPUT


class TestCERTBundRuleExpertBot(test.BotTestCase, unittest.TestCase):
    """
    A TestCase for CERTBundRuleExpertBot.
    """

    @classmethod
    def set_bot(cls):
        cls.bot_reference = CERTBundRuleExpertBot
        cls.temp_rules_dir = TemporaryDirectory()
        cls.sysconfig = {'script_directory': cls.temp_rules_dir.name}
        cls.default_input_message = SOURCE_CONTACTS_EXAMPLE_INPUT
        cls.allowed_warning_count = 1

    @classmethod
    def tearDownClass(cls):
        cls.temp_rules_dir.cleanup()

    def test_source_contacts(self):
        self.input_message = SOURCE_CONTACTS_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, SOURCE_CONTACTS_EXAMPLE_OUTPUT)

    def test_empty_source_directives(self):
        self.input_message = EMPTY_SOURCE_DIRECTIVES_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, EMPTY_SOURCE_DIRECTIVES_EXAMPLE_OUTPUT)

    def test_non_empty_certbund(self):
        self.input_message = NON_EMPTY_CERTBUND_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, NON_EMPTY_CERTBUND_EXAMPLE_OUTPUT)


if __name__ == "__main__":
    unittest.main()
