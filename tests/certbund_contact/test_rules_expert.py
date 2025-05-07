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

EMPTY_SOURCE_DIRECTIVES_EXAMPLE_OUTPUT = SOURCE_CONTACTS_EXAMPLE_OUTPUT

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

    def test_remove_source_contacts(self):
        """ Should remove source_contacts """
        self.input_message = SOURCE_CONTACTS_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, SOURCE_CONTACTS_EXAMPLE_OUTPUT)

    def test_not_remove_source_contacts(self):
        """ Should not remove source_contacts with remove_contact_data False """
        self.input_message = SOURCE_CONTACTS_EXAMPLE_INPUT
        self.run_bot(parameters={'remove_contact_data': False})
        self.assertMessageEqual(0, SOURCE_CONTACTS_EXAMPLE_INPUT)

    def test_remove_empty_source_directives(self):
        self.input_message = EMPTY_SOURCE_DIRECTIVES_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, EMPTY_SOURCE_DIRECTIVES_EXAMPLE_OUTPUT)

    def test_non_empty_certbund(self):
        self.input_message = NON_EMPTY_CERTBUND_EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, NON_EMPTY_CERTBUND_EXAMPLE_OUTPUT)

    def test_nonexisting_script_directory(self):
        self.allowed_warning_count = 0
        # not a directory
        with self.assertRaisesRegex(ValueError, expected_regex='.*is not a directory or cannot be read.*'):
            self.run_bot(parameters={'script_directory': '/dev/null'})
        # missing read permissions
        with self.assertRaisesRegex(ValueError, expected_regex='.*is not a directory or cannot be read.*'):
            self.run_bot(parameters={'script_directory': '/root/.ssh/'})

    def test_empty_script_directory(self):
        """ Empty dir should give a warning, message should be passed through """
        self.allowed_warning_count = 1  # No rules loaded
        self.input_message = SOURCE_CONTACTS_EXAMPLE_OUTPUT
        with TemporaryDirectory() as tempdir:
            self.run_bot(parameters={'script_directory': tempdir})
        self.assertMessageEqual(0, SOURCE_CONTACTS_EXAMPLE_OUTPUT)
        self.assertLogMatches('No rules loaded\.', 'WARNING')


if __name__ == "__main__":
    unittest.main()
