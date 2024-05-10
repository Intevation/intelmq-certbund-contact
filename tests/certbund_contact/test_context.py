# -*- coding: utf-8 -*-

"""
Testing Context
"""

import unittest

from intelmq.lib.message import Event

from intelmq_certbund_contact.rulesupport import \
    Context

EXAMPLE_EVENT = Event({"time.observation": "2024-05-08T03:37:05+00:00", "time.source": "2024-05-07T02:23:39+00:00",
                       "source.ip": "192.0.2.1",
                       "extra.certbund": {"source_contacts": {
                           "matches": [
                               {"annotations": [], "field": "asn", "managed": "manual", "organisations": [0]}],
                           "organisations": [
                               {"annotations": [],
                                "contacts": [{
                                    "annotations": [],
                                    "email": "abuse@example.com", "email_status": "enabled", "managed": "automatic"}],
                                   "id": 0, "import_source": "ripe", "managed": "automatic", "name": "Example", "sector": None},
                           ]}}})


class TestContext(unittest.TestCase):

    def test_ensure_data_consistency_match_set(self):
        """
        Check if Context.ensure_data_consistency ensures that matches is always a list
        """
        event = EXAMPLE_EVENT
        context = Context(event, section='source', base_logger=None)
        context.matches = set(context.matches)
        self.assertIsInstance(context.matches, list)


if __name__ == "__main__":
    unittest.main()
