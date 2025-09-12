# -*- coding: utf-8 -*-

"""
Testing certbund_contact.eventjson
"""

import unittest
from copy import deepcopy
from json import dumps
from intelmq.lib.message import Event

import intelmq_certbund_contact.eventjson as eventjson


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


def del_certbund_field(event, key):
    """
    A better testable version of the function: has a return value
    """
    new_event = deepcopy(event)
    eventjson.del_certbund_field(new_event, key)
    return new_event


class TestEventJSON(unittest.TestCase):
    """
    A TestCase for intelmq_certbund_contact.eventjson.
    """

    def test_del_certbund_field(self):
        # should do nothing
        event = Event({'comment': '1'})
        self.assertEqual(del_certbund_field(event, '2'), event)
        event = Event({'extra': dumps({'comment': '2'})})
        self.assertEqual(del_certbund_field(event, '2'), event)
        event = Event({'extra': dumps({'comment': '2'})})
        self.assertEqual(del_certbund_field(event, '1'), event)
        # should remove the field
        event = Event({'extra': dumps({'certbund': {'a': 2}})})
        self.assertEqual(del_certbund_field(event, 'a'), {})
        event = Event({'extra': dumps({'certbund': {'a': 2}, 'blocklist': 'lorem'})})
        self.assertEqual(del_certbund_field(event, 'a'), {'extra.blocklist': 'lorem'})


if __name__ == "__main__":
    unittest.main()
