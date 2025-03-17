"""
Tests ripe_data.py

Copyright (C) 2025 by Bundesamt für Sicherheit in der Informationstechnik
Software engineering by Intevation GmbH
"""

import unittest
from copy import deepcopy
from json import dumps
import logging
from os.path import dirname

from intelmq.lib.message import Event

from intelmq_certbund_contact.ripe import ripe_data


class TestRipeData(unittest.TestCase):
    """
    Some special cases in RIPE data parsing (2auto/issue91 and 2auto/issue354)
    """

    maxDiff = None

    def test_role_simple(self):
        role_list = ripe_data.parse_file(
            f"{dirname(__file__)}/role_simple.txt.gz",
            ("role", "nic-hdl", "abuse-mailbox", "org"),
            verbose=True,
        )
        sanitized = [dict(element) for element in ripe_data.sanitize_role_list(role_list)]
        self.assertEqual(
            sanitized,
            [
                {
                    "abuse-mailbox": ["null@example.com"],
                    "nic-hdl": ["ACRO6281-RIPE"],
                    "role": ["Null"],
                }
            ],
        )

    def test_role_display_name_format(self):
        """
        Examples in RIPE Data:
        abuse-mailbox:  abuse@icloudhosting.com <abuse@icloudhosting.com>
        abuse-mailbox:  abuse-lignesreseau@sigdci76.fr <abuse-lignesreseau@sigdci76.fr>
        abuse-mailbox:  abuse@novaposhta.ua  <abuse@novaposhta.ua>
        abuse-mailbox:  n.issart@ville-arles.fr <n.issart@ville-arles.fr>
        """
        role_list = ripe_data.parse_file(
            f"{dirname(__file__)}/role_display_name.txt.gz",
            ("role", "nic-hdl", "abuse-mailbox", "org"),
            verbose=True,
        )
        sanitized = [dict(element) for element in ripe_data.sanitize_role_list(role_list)]
        self.assertEqual(
            sanitized,
            [
                {
                    "abuse-mailbox": ["abuse@novaposhta.ua"],
                    "nic-hdl": ["NN2241-RIPE"],
                    "role": ["NOVAPOSHTA NOC"],
                },
                {
                    "abuse-mailbox": ["abuse@icloudhosting.com"],
                    "nic-hdl": ["BBSA1-RIPE"],
                    "role": ["BBS Admin-c"],
                },
            ],
        )

    def test_role_special_characters(self):
        """
        Examples in RIPE data:
        abuse-mailbox:  gedeeldeinfra&staven@vgz.nl
        abuse-mailbox:  "r:[/r/]*4;e'*&m'"@fenix.international
        abuse-mailbox:  N&INetworkOperations@homeoffice.gov.uk
        abuse-mailbox:  sdm.n&c@frieslandcampina.com
        abuse-mailbox:  kevino'connor@merseyfire.gov.uk
        No examples in RIPE data, but allowed: whitespaces in the local part
        abuse-mailbox:  "foo bar"@example.com
        """
        role_list = ripe_data.parse_file(
            f"{dirname(__file__)}/role_special_characters.txt.gz",
            ("role", "nic-hdl", "abuse-mailbox", "org"),
            verbose=True,
        )
        sanitized = [dict(element) for element in ripe_data.sanitize_role_list(role_list)]
        self.assertEqual(
            sanitized,
            [
                {
                    "abuse-mailbox": ['"r:[/r/]*4;e\'*&m\'"@fenix.international'],
                    "nic-hdl": ["AR19875-RIPE"],
                    "role": ["Abuse-C Role"],
                    'org': ['ORG-EFHB1-RIPE'],
                },
                {
                    "abuse-mailbox": ['"abuse contact"@example.com'],
                    "nic-hdl": ["DUMY1-RIPE"],
                    "role": ["Non-existing contact with white space"],
                },
            ],
        )

    def test_trailing_comment(self):
        """
        Examples in RIPE data:
        abuse-mailbox:  abuse@crimeainfo.com,
        abuse-mailbox:  abuse@cxl.zone (preferred)
        """
        role_list = ripe_data.parse_file(
            f"{dirname(__file__)}/role_trailing_comment.txt.gz",
            ("role", "nic-hdl", "abuse-mailbox", "org"),
            verbose=True,
        )
        sanitized = [dict(element) for element in ripe_data.sanitize_role_list(role_list)]
        self.assertEqual(
            sanitized,
            [
                {
                    "abuse-mailbox": ['abuse@crimeainfo.com'],
                    "nic-hdl": ["AR20626-RIPE"],
                    "role": ["Abuse-C Role"],
                    'org': ['ORG-CINF1-RIPE'],
                },
                {
                    "abuse-mailbox": ['abuse@cxl.zone'],
                    "nic-hdl": ["CC22562-RIPE"],
                    "role": ["CXLNet Contacts"],
                }
            ],
        )

    def test_multiple_addresses(self):
        """
        There are no examples in RIPE data as of 2025-03-05 but it should still be parseable:
        abuse-mailbox:  abuse@example.com abuse@example.net
        abuse-mailbox:  abuse@example.com, abuse@example.net
        One address with whitespace in local part and also a second address separated by a white space:
        abuse-mailbox:  "abuse contact"@example.com abuse@example.com
        """
        role_list = ripe_data.parse_file(
            f"{dirname(__file__)}/role_multiple_addresses.txt.gz",
            ("role", "nic-hdl", "abuse-mailbox", "org"),
            verbose=True,
        )
        sanitized = [dict(element) for element in ripe_data.sanitize_role_list(role_list)]
        self.assertEqual(
            sanitized,
            [
                {
                    "abuse-mailbox": ['abuse@example.com', 'abuse@example.net'],
                    "nic-hdl": ["DUMY1-RIPE"],
                    "role": ["Non-existing contact 1"],
                },
                {
                    "abuse-mailbox": ['abuse@example.com', 'abuse@example.net'],
                    "nic-hdl": ["DUMY2-RIPE"],
                    "role": ["Non-existing contact 2 with comma"],
                },
                {
                    "abuse-mailbox": ['"abuse contact"@example.com', 'abuse@example.com'],
                    "nic-hdl": ["DUMY3-RIPE"],
                    "role": ["Non-existing contacts with white-space"],
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
