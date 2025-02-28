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

IN_MULTIPLE_SAME_ORG = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [0]
                }, {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [1],
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"},
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.com", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 1, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }
            ]
        }
    },
})
OUT_MULTIPLE_SAME_ORG = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [0, 2]
                }, {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [1, 3],
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"},
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.com", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 1, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}],
                            "email": "gov@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 2, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Government", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}],
                            "email": "gov@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 3, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Government", "sector": None
                }
            ]
        }
    },
})

IN_MULTIPLE_MULTIPLE_ORG = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [0]
                }, {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [1],
                }, {
                    "address": "172.16.0.0/20", "annotations": [], "field": "ip", "managed": "manual", "organisations": [2]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 1, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:finance"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@finance.example", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 2, "import_source": "ripe", "managed": "automatic", "name": "finance.example", "sector": None
                }
            ]
        }
    },
})
OUT_MULTIPLE_MULTIPLE_ORG = Event({
    "extra.certbund": {
        "source_contacts": {
            "matches": [
                {
                    "address": "172.16.0.0/12", "annotations": [], "field": "ip", "managed": "manual", "organisations": [0, 3]
                }, {
                    "annotations": [], "field": "asn", "managed": "automatic", "organisations": [1, 4],
                }, {
                    "address": "172.16.0.0/20", "annotations": [], "field": "ip", "managed": "manual", "organisations": [2, 5]
                }
            ],
            "organisations": [
                {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 0, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": "Constituency:government"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@example.net", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 1, "import_source": "ripe", "managed": "automatic", "name": "example.net", "sector": None
                }, {
                    "annotations": [], "contacts": [
                            {"annotations": [{"tag": "Constituency:finance"}, {"tag": "Format:CSV_inline"}],
                            "email": "abuse@finance.example", "email_status": "enabled", "managed": "automatic"}
                    ], "id": 2, "import_source": "ripe", "managed": "automatic", "name": "finance.example", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}],
                            "email": "gov@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 3, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Government", "sector": None
                }, {
                    "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:government', 'condition': True}],
                            "email": "gov@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 4, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Government", "sector": None
                }, {
                    "annotations": [], "annotations": [], "contacts": [{"annotations": [{"tag": 'Format:CSV_inline', 'condition': True}, {"tag": 'Constituency:finance', 'condition': True}],
                            "email": "finance@cert.example", "email_status": "enabled", "managed": "manual"}
                    ], "id": 5, "import_source": "21constituency_copies.py", "managed": "manual", "name": "Copy Finance", "sector": None
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
        """ internal requirement source: msg5122 """
        in_context = Context(IN_SIMPLE, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_SIMPLE, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))

    def test_multiple_same_org(self):
        """ internal requirement source: msg5126
        Multiple contacts in one organization"""
        in_context = Context(IN_MULTIPLE_SAME_ORG, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_MULTIPLE_SAME_ORG, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))

    def test_multiple_multiple_org(self):
        """ internal requirement source: msg5142 msg5143
        Multiple organisations with different CIDR- and AS-matches cause each a copy"""
        in_context = Context(IN_MULTIPLE_MULTIPLE_ORG, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_MULTIPLE_MULTIPLE_ORG, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))

    def test_multiple(self):
        in_context = Context(IN_MULTIPLE, "source", base_logger=logging.getLogger(__name__))
        out_context = Context(OUT_MULTIPLE, "source", base_logger=logging.getLogger(__name__))
        new_context = deepcopy(in_context)
        constituency_copies.determine_directives(new_context)
        self.assertEqual(repr(new_context.organisations), repr(out_context.organisations))
        self.assertEqual(repr(new_context.matches), repr(out_context.matches))

if __name__ == "__main__":
    unittest.main()
