# -*- coding: utf-8 -*-

"""
Testing certbund_contact
"""

from __future__ import unicode_literals
from copy import deepcopy

import unittest

import intelmq.lib.test as test
from intelmq_certbund_contact.bots.experts.certbund_contact.expert import CERTBundKontaktExpertBot, common


EXAMPLE_INPUT = {"__type": "Event",
                 "source.ip": "192.168.42.23",
                 "destination.ip": "192.168.42.47",
                 "time.observation": "2016-02-26T10:11:12+00:00",
                 "feed.name": "test",
                 "raw": "",
                 "classification.type": "other"
                 }

EXAMPLE_OUTPUT = {
    "__type": "Event",
    "source.ip": "192.168.42.23",
    "destination.ip": "192.168.42.47",
    "time.observation": "2016-02-26T10:11:12+00:00",
    "feed.name": "test",
    "classification.type": "other",
    'extra.certbund': {"source_contacts": {
              "matches": [
              {"address": "192.168.42.0/24", "field": "ip",
               "managed": "automatic", "organisations": [0]
              },
              {"field": "fqdn", "managed": "manual", "organisations": [1]}
              ],
              "organisations": [
              {"annotations": [{"type": "tag", "value": "daily"}],
               "contacts": [
              {"email": "someone@example.com", "email_status": "disabled",
               "managed": "automatic"}
              ],
               "id": 0, "managed": "automatic",
               "name": "Some Organisation", "sector": None
              },
              {"annotations": [{"type": "tag", "value": ""}],
               "contacts": [
              {"email": "other@example.com", "email_status": "enabled",
               "managed": "manual"}
              ],
               "id": 1, "managed": "manual", "name": "Another Organisation",
               "sector": "IT"}]},
    }}



ORGS1 = [
    {"annotations": [],
        "contacts": [{"annotations": [{"tag": "Target group:Some"}], "email": "automatic@example.com", "email_status": "enabled", "managed": "automatic"}],
        "id": 0, "import_source": "ripe", "managed": "automatic", "name": "Org Name", "sector": None
    },
    {"annotations": [],
        "contacts": [{"annotations": [{"tag": "Target group:Some"}], "email": "manual1@example.com", "email_status": "enabled", "managed": "manual"}],
        "id": 1, "import_source": "", "managed": "manual", "name": "Org Name", "sector": None
    },
    {"annotations": [],
        "contacts": [{"annotations": [{"tag": "Target group:Some"}], "email": "manual2@example.com", "email_status": "enabled", "managed": "manual"}],
        "id": 2, "import_source": "", "managed": "manual", "name": "Org Name", "sector": None
    }
]


class CERTBundKontaktMockDBExpertBot(CERTBundKontaktExpertBot):
    """CERTBundKontaktExpertBot that mocks all database accesses"""

    def connect_to_database(self):
        pass

    def lookup_contact(self, ip, fqdn, asn, country_code):
        if ip.startswith("192.168.42."):
            return {"matches": [{"field": "ip", "managed": "automatic",
                                 "address": "192.168.42.0/24",
                                 "organisations": [0]},
                                {"field": "fqdn", "managed": "manual",
                                 "organisations": [1]}],
                    "organisations": [
                        {"id": 0,
                         "name": "Some Organisation",
                         "managed": "automatic",
                         "sector": None,
                         "annotations": [{"type": "tag", "value": "daily"}],
                         "contacts": [{
                             "email": "someone@example.com",
                             "managed": "automatic",
                             "email_status": "disabled"
                             }],
                         },
                        {"id": 1,
                         "name": "Another Organisation",
                         "managed": "manual",
                         "sector": "IT",
                         "annotations": [{"type": "tag", "value": ""}],
                         "contacts": [{
                             "email": "other@example.com",
                             "managed": "manual",
                             "email_status": "enabled"
                             }],
                         }]
                    }
        elif ip == "127.0.0.10":
            return {"organisations": ORGS1,
                    "matches": [
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "automatic", "organisations": [0]},
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "manual", "organisations": [2]},
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "manual", "organisations": [1]}
                    ]}
        return {"matches": [], "organisations": []}

RENUMBER_INPUT = {'organisations': [{'id': 72, 'name': 'TP Global Operations Limited', 'sector': None, 'contacts': [{'email': 'abuse@truphone.com', 'managed': 'automatic', 'email_status': 'enabled', 'annotations': [{'tag': 'Constituency:ISP'}, {'tag': 'Format:CSV_inline'}]}], 'annotations': [], 'managed': 'automatic', 'import_source': 'ripe'}], 'matches': [{'field': 'ip', 'address': '185.99.26.180/30', 'organisations': [72], 'annotations': [], 'managed': 'automatic'}]}
RENUMBER_OUTPUT = {'organisations': [{'id': 0, 'name': 'TP Global Operations Limited', 'sector': None, 'contacts': [{'email': 'abuse@truphone.com', 'managed': 'automatic', 'email_status': 'enabled', 'annotations': [{'tag': 'Constituency:ISP'}, {'tag': 'Format:CSV_inline'}]}], 'annotations': [], 'managed': 'automatic', 'import_source': 'ripe'}], 'matches': [{'field': 'ip', 'address': '185.99.26.180/30', 'organisations': [0], 'annotations': [], 'managed': 'automatic'}]}



class TestCERTBundKontaktMockDBExpertBot(test.BotTestCase, unittest.TestCase):
    """
    A TestCase for TestCERTBundKontaktMockDBExpertBot.
    """

    @classmethod
    def set_bot(cls):
        cls.bot_reference = CERTBundKontaktMockDBExpertBot
        cls.default_input_message = EXAMPLE_INPUT

    def test_ipv4_lookup(self):
        self.input_message = EXAMPLE_INPUT
        self.run_bot()
        self.assertMessageEqual(0, EXAMPLE_OUTPUT)

    def test_renumber_organisations_in_place(self):
        self.prepare_bot()
        msg = deepcopy(RENUMBER_INPUT)
        self.bot.renumber_organisations_in_place(msg)
        self.assertEqual(msg, RENUMBER_OUTPUT)
        self.input_queue = []

    def test_renumber_organisations_in_place_merge(self):
        """ Assert that identical matches are merged """
        self.prepare_bot()
        msg = {"organisations": deepcopy(ORGS1),
                    "matches": [
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "automatic", "organisations": [0]},
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "manual", "organisations": [2]},
                        {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "manual", "organisations": [1]}
                    ]}
        self.bot.renumber_organisations_in_place(msg)
        self.assertEqual(msg,
            {"organisations": ORGS1,
                "matches": [
                    {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "automatic", "organisations": [0]},
                    {"address": "127.0.0.0/30", "annotations": [], "field": "ip", "managed": "manual", "organisations": [1, 2]},
                ]}
            )
        self.input_queue = []

if __name__ == "__main__":
    unittest.main()
