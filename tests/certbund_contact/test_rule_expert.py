"""
Testing certbund_contact rules expert bot
"""

import tempfile
import unittest

import intelmq.lib.test as test
from intelmq_certbund_contact.bots.experts.certbund_rules.expert import CERTBundRuleExpertBot


EMPTY_EVENT = {"__type": "Event", "source.as_name": "Example AS"}


class TestCERTBundRuleExpertBot(test.BotTestCase, unittest.TestCase):
    @classmethod
    def set_bot(cls):
        cls.bot_reference = CERTBundRuleExpertBot
        cls.default_input_message = EMPTY_EVENT

    def test_nonexisting_script_directory(self):
        self.allowed_warning_count = 0
        # not a directory
        with self.assertRaisesRegex(ValueError, expected_regex='.*is not a directory or cannot be read.*'):
            self.run_bot(parameters={'script_directory': '/dev/null'})
        # missing read permissions
        with self.assertRaisesRegex(ValueError, expected_regex='.*is not a directory or cannot be read.*'):
            self.run_bot(parameters={'script_directory': '/root/.ssh/'})

    def test_empty(self):
        """ Empty dir should give a warning, empty message should be passed through """
        self.allowed_warning_count = 1  # No rules loaded
        with tempfile.TemporaryDirectory() as tempdir:
            self.run_bot(parameters={'script_directory': tempdir})
        self.assertMessageEqual(0, EMPTY_EVENT)
        self.assertLogMatches('No rules loaded\.', 'WARNING')


if __name__ == "__main__":
    unittest.main()
