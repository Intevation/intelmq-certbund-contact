"""
Tests 21_constituency_copies

Copyright (C) 2024-2025 by Bundesamt für Sicherheit in der Informationstechnik
Software engineering by Intevation GmbH
"""

import unittest
from copy import deepcopy
from json import dumps
import logging
from os.path import dirname

from intelmq.lib.message import Event

from intelmq_certbund_contact.rulesupport import \
     Context, keep_most_specific_contacts, Organisation, Contact
from intelmq_certbund_contact.annotations import Annotation, Const

from intelmq_certbund_contact.eventjson import \
     set_certbund_contacts

from importlib.machinery import SourceFileLoader
constituency_copies = SourceFileLoader("module.name", f"{dirname(__file__)}/../../../example-rules/21constituency_copies.py").load_module()

IN_SIMPLE = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [0]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }
            ]
        }
    },
})
OUT_SIMPLE = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [0, 1]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}],
                            "email": "gov@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 1, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Government", "sector": None
                }
            ]
        }
    },
})

IN_MULTIPLE = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [0]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "automatic", "organisations": [0]
                }, {
                    "annotations": [], "field": "asn", "managed": "manual", "organisations": [2]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [1]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [3]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:network_operators"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.com", "email_status": "enabled", "managed": "manual"}
                    ], "id": 1, "import_source": "", "managed": "manual", "name": "Test Gov CIDR 172.16.0.0/12", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "as64496@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 2, "import_source": "", "managed": "manual", "name": "Test AS64496", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:CNI_energy"}, {"tag": "Format:CSV_inline"}],
                            "email": "critical@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 3, "import_source": "", "managed": "manual", "name": "Test CNI_energy CIDR 172.16.0.0/12", "sector": None
                }
            ]
        }
    },
})
OUT_MULTIPLE = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [0, 4]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "automatic", "organisations": [0]
                }, {
                    "annotations": [], "field": "asn", "managed": "manual", "organisations": [2, 6]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [1, 5]
                }, {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [3]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:network_operators"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.com", "email_status": "enabled", "managed": "manual"}
                    ], "id": 1, "import_source": "", "managed": "manual", "name": "Test Gov CIDR 172.16.0.0/12", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "as64496@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 2, "import_source": "", "managed": "manual", "name": "Test AS64496", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:CNI_energy"}, {"tag": "Format:CSV_inline"}],
                            "email": "critical@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 3, "import_source": "", "managed": "manual", "name": "Test CNI_energy CIDR 172.16.0.0/12", "sector": None
                }, {
                    "annotations": [], "contacts": [{"email": 'isp@cert.example', "managed": 'manual', "email_status": 'enabled', "annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:network_operators', 'condition': True}]}],
                    "id": 4, "import_source": '21constituency_copies.py', "managed":'manual', "name": 'Copy Network Operators', "sector": None
                }, {
                     "annotations": [], "contacts": [{"email": 'gov@cert.example', "managed":'manual', "email_status": 'enabled', "annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}]}],
                     "id": 5, "name":'Copy Government', "managed":'manual', "import_source": '21constituency_copies.py', "sector": None,
                }, {
                     "annotations": [], "contacts": [{"email": 'gov@cert.example', "managed":'manual', "email_status": 'enabled', "annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}]}],
                     "id": 6, "name":'Copy Government', "managed":'manual', "import_source": '21constituency_copies.py', "sector": None,
                }
            ]
        }
    },
})

class TestRule(unittest.TestCase):

    maxDiff = None

    def test_simple(self):
        in_context = Context(IN_SIMPLE, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_SIMPLE, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))

    def test_default(self):
        in_context = Context(IN_MULTIPLE, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_MULTIPLE, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))

if __name__ == "__main__":
    unittest.main()
