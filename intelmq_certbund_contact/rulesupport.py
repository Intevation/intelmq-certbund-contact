"""Provide common functions to handle notification rules.

Copyright (C) 2016, 2017 by Bundesamt für Sicherheit in der Informationstechnik
Software engineering by Intevation GmbH

This program is Free Software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>.

Author(s):
    Bernhard Herzog <bernhard.herzog@intevation.de>
    Dustin Demuth <dustin.demuth@intevation.de>
"""
from contextlib import contextmanager
from collections import defaultdict
from itertools import chain

from intelmq_certbund_contact.eventjson import get_certbund_contacts, \
    set_certbund_directives
import intelmq_certbund_contact.annotations as annotations


class Organisation:

    """An organisation

    Attributes:
        orgid (int): ID that is used to refer to the organisation from
            the matches and potentially other places.
        name (str): Name of the organisation
        managed (str): Either 'manual' or 'automatic' indicating how the
            contact database entry is managed.
        import_source (str): The source from which the data was imported
            into the contact database. Only valid if managed is
            'automatic'.
        sector (str): The sector of the organisation (e.g. 'IT',
            'Energe' or similar)
        contacts (list of Contact): The contacts associated with the
            organisation. Notifications related to the organisation
            should be sent to one or more of these.
        annotations (list of Annotation): The annotations associated
            with organisation.
    """

    def __init__(self, orgid, name, managed, import_source, sector, contacts,
                 annotations):
        self.orgid = orgid
        self.name = name
        self.managed = managed
        self.import_source = import_source
        self.sector = sector
        self.contacts = contacts
        self.annotations = annotations

    def __repr__(self):
        return ("Organisation(orgid=%r, name=%r, managed=%r, import_source=%r,"
                " sector=%r, contacts=%r, annotations=%r)"
                % (self.orgid, self.name, self.managed, self.import_source,
                   self.sector, self.contacts, self.annotations))

    @classmethod
    def from_json(cls, jsondict):
        return cls(orgid=jsondict["id"],
                   name=jsondict["name"],
                   managed=jsondict["managed"],
                   import_source=jsondict.get("import_source", ""),
                   sector=jsondict["sector"],
                   contacts=[Contact.from_json(c)
                             for c in jsondict["contacts"]],
                   annotations=[annotations.from_json(a)
                                for a in jsondict["annotations"]])

    def all_annotations(self):
        """Return an iterator over all annotations of the organisation.

        This includes the annotations associated with the organisation
        itself and the annotations associated with the contacts.
        """
        for annotation in self.annotations:
            yield annotation
        for contact in self.contacts:
            for annotation in contact.annotations:
                yield annotation


class Contact:

    """Contact details.

    Attributes:
        email (str): email address
        managed (str): Either 'manual' or 'automatic' indicating how the
            contact database entry is managed.
        email_status (str): Either 'enabled' or 'disabled'. 'disabled'
            usually means that the email address is likely invalid in
            some way, e.g. because emails sent there bounce.
        annotations (list of Annotation): The annotations associated
            with the contact.
    """

    def __init__(self, email, managed, email_status="enabled",
                 annotations=None):
        self.email = email
        self.managed = managed
        self.email_status = email_status
        self.annotations = annotations if annotations is not None else []

    def __repr__(self):
        return ("Contact(email=%r, managed=%r, email_status=%r, annotations=%r)"
                % (self.email, self.managed, self.email_status,
                   self.annotations))

    @classmethod
    def from_json(cls, jsondict):
        return cls(email=jsondict["email"],
                   managed=jsondict["managed"],
                   email_status=jsondict.get("email_status", "enabled"),
                   annotations=[annotations.from_json(a)
                                for a in jsondict.get("annotations", ())])


class Match:

    """A reason why an event matched an entry in the contact database.

    Attributes:

        field (str): The name of the event field that matched

        managed (str): Either 'manual' or 'automatic' indicating how the
            contact database entry is managed.

        organisations (list of int): The IDs of the organisations
            associated with the matching entry

        annotations (list of Annotation): The annotations associated
            with the database match entry. These annotations are the
            ones directly associated with the matching entry in the DB,
            e.g. the ASN entry if the field refers to an ASN. Other
            matches may contain other annotations.

        address (str or None): the network address that matched if the
            field is either 'source.ip' or 'destination.ip'. None
            otherwise.
    """

    def __init__(self, field, managed, organisations, annotations,
                 address=None):
        self.field = field
        self.managed = managed
        self.organisations = organisations
        self.annotations = annotations
        self.address = address

    def __repr__(self):
        return ("Match(field=%r, managed=%r, organisations=%r, annotations=%r,"
                " address=%r)"
                % (self.field, self.managed, self.organisations,
                   self.annotations, self.address))

    def __eq__(self, other):
        return (self.field == other.field and
                self.managed == other.managed and
                self.organisations == other.organisations and
                self.annotations == other.annotations and
                self.address == other.address)

    def __hash__(self):
        return hash((self.field, self.managed, tuple(self.organisations),
                     tuple(self.annotations), self.address))

    @classmethod
    def from_json(cls, jsondict):
        field = jsondict["field"]
        if field == "ip":
            address = jsondict["address"]
        else:
            address = None
        return cls(field=field,
                   managed=jsondict["managed"],
                   organisations=jsondict["organisations"],
                   annotations=[annotations.from_json(a)
                                for a in jsondict["annotations"]],
                   address=address)


class Directive:

    """Notification directive

    A notification directive indicates to other components, e.g.
    intelmq-mailgen, which notifications should be sent where based on
    the event the directive is associated with.

    Attributes:
        medium (str): The transport medium for the notification.
            So far, only "email" is implemented. More will likely come, such
            as "xmpp"
        recipient_address (str): medium-specific address.
            For email, the email address, obviously.
        aggregate_fields (set of str): Set of event field names that are
            to be part of the aggregate identifier. See aggregation,
            below.
        aggregate_key (dict): Key/value pairs to be part of the
            aggregate identifier. See aggregation, below.
        notification_interval (int): Interval between notifications for
            similar events. Two events are considered similar in this
            sense if they have equal aggregate identifiers.
        notification_format (str): The main format of the notification.
            Suggested values: ``"text"`` for human readable mail with
            e.g. event data inline or as attachment, ``"xarf"`` for
            mail in X-ARF format.
        event_data_format (str): The format to use for event data
            included in the notification. Its meaning depends on the
            notification format.
        template_name (str): The name of the template for the contents
            of the notification. Its meaning depends on the notification
            format. Mostly useful for human readable (parts of)
            notifications, e.g. text email or the human readable part of
            X-ARF mails.

    **Aggregation**

    Multiple notification directives may be aggregated into a single
    notification. Directives may only be aggregated when they are
    sufficiently similar. Not only do they have to be sent to the same
    recipient using the same medium and format, often they must also be
    similar enough in other respects, e.g. by being related to the same
    ASN.

    This similarity is defined with the aggregation identifier which is
    conceptually a set of key/value pairs (set in the sense that each
    key must occur only once). Directives with equal aggregation
    identifiers may be aggregated because they are considered to
    sufficiently similar. Some parts of it are implicit, such as a the
    parameters for the more physical aspects of the notification (e.g.
    medium, address, etc.). The other parts have to be handled
    explicitly. In this class this is done with the two attributes
    :py:attr:`aggregate_key` and :py:attr:`aggregate_fields`. The former
    is a dict whose contents are simply treated as part of the
    aggregation identifier. The latter is a set of event field names and
    these names together with the corresponding values from the event
    are also treated as part of the aggregation identifier. The
    aggregate_fields attribute is mainly meant for convenience so that
    one does not have to copy the actual attributes explicitly.


    **JSON-Representation**

    When converted to JSON, a directive is a JSON-Object whose keys and
    values are the public attributes of the Directive instance with the
    exception of :py:attr:`aggregate_fields` and
    :py:attr:`aggregate_key`, which are combined into a single
    dictionary in the obvious way and included in the JSON object under
    the key ``"aggregate_identifier"``.
    """

    def __init__(self, medium=None, recipient_address=None,
                 aggregate_fields=(), aggregate_key=(),
                 notification_interval=None, notification_format=None,
                 event_data_format=None, template_name=None):
        self.medium = medium
        self.recipient_address = recipient_address
        self.aggregate_fields = set(aggregate_fields)
        self.aggregate_key = dict(aggregate_key)
        self.notification_interval = notification_interval
        self.notification_format = notification_format
        self.event_data_format = event_data_format
        self.template_name = template_name

    def __repr__(self):
        return ("Directive(medium={medium!a},"
                " recipient_address={recipient_address!a},"
                " aggregate_fields={aggregate_fields!a},"
                " aggregate_key={aggregate_key!a},"
                " notification_interval={notification_interval!a},"
                " notification_format={notification_format!a},"
                " event_data_format={event_data_format!a},"
                " template_name={template_name!a})"
                .format(**self.__dict__))

    def __eq__(self, other):
        return (self.medium == other.medium and
                self.recipient_address == other.recipient_address and
                self.aggregate_fields == other.aggregate_fields and
                self.aggregate_key == other.aggregate_key and
                self.notification_interval == other.notification_interval and
                self.notification_format == other.notification_format and
                self.event_data_format == other.event_data_format and
                self.template_name == other.template_name)

    def __hash__(self):
        return hash((self.medium,
                     self.recipient_address,
                     self.aggregate_fields,
                     self.aggregate_key,
                     self.notification_interval,
                     self.notification_format,
                     self.event_data_format,
                     self.template_name))

    @classmethod
    def from_contact(cls, contact, **kw):
        """Create a new directive from a email contact.
        The new directive will define "email" as medium and use the
        contact's email attribute as the recipient_address.
        """
        return cls(recipient_address=contact.email, medium="email", **kw)

    def as_dict_for_event(self, event):
        """Return a dictionary that can be attached to the given event.

        Args:
            event: The event from which to take the values indicated by
                :py:attr:`aggregate_fields`

        Returns:
            A dict that can be included in the e.g. the event's extra
            dictionary and serialized to JSON in the way described in
            the class doc-string.
        """
        aggregate_identifier = self.aggregate_key.copy()
        for field in self.aggregate_fields:
            aggregate_identifier[field] = event.get(field)

        return dict(medium=self.medium,
                    recipient_address=self.recipient_address,
                    aggregate_identifier=aggregate_identifier,
                    notification_interval=self.notification_interval,
                    notification_format=self.notification_format,
                    event_data_format=self.event_data_format,
                    template_name=self.template_name)

    def aggregate_by_field(self, fieldname):
        """Indicate that aggregation should consider the given event field.

        Args:
            fieldname (str): The name of the event field whose value
                must be equal in two directives if they are to be
                aggregated.

        The fieldname is added to the :py:attr:`aggregate_fields`
        attribute.
        """
        self.aggregate_fields.add(fieldname)

    def update(self, directive):
        """Update self with the attributes of another directive.

        Most attributes are simply copied if their value is not None,
        however, for aggregate_fields and aggregate_key the other
        directive's values are added to self's values with the
        respective update method.

        This is useful when writing scripts where one wants to combine
        attributes that depend mainly on the event's contents, e.g.
        which feed it came from or the event's classification, and
        attributes taken from the contact information. For example::

            def determine_directives(context):
                feed_directive = directive_from_feed(context.get("feed.name"))
                if feed_directive is not None:
                    for contact in context.all_contacts():
                        directive = Directive.from_contact(contact)
                        directive.update(feed_directive)
                        context.add_directive(directive)
                return True
        """
        for attr in ["medium", "recipient_address", "notification_interval",
                     "notification_format", "event_data_format",
                     "template_name"]:
            new = getattr(directive, attr)
            if new is not None:
                setattr(self, attr, new)
        self.aggregate_fields.update(directive.aggregate_fields)
        self.aggregate_key.update(directive.aggregate_key)


def contact_info_from_json(jsondict):
    return ([Match.from_json(m) for m in jsondict["matches"]],
            [Organisation.from_json(o) for o in jsondict["organisations"]])


class Context:

    """Context given to rule scripts

    The context object provides access to various pieces of information
    the scripts need and collects the directives created by the scripts.
    It's a single object so that it's easy to add more information. We
    only need to add a new attribute to the context instead of add a new
    parameter to all scripts.

    The public attributes are listed below. You may assign new lists to
    ``matches`` and ``organisations`` from a script in order to e.g.
    reduce the contact information available to scripts that run later
    by removing all but the most relevant matches and contacts. Try not
    to modify the lists in-place, though. Assigning to them triggers
    some cleanup procedures that make sure the references from matches
    to organisation stay consistent.

    Attributes:
        section (str): Either ``'source'`` when the script is called due
            to matches in the source attributes (e.g. ``"source.ip"``,
            ``"source.asn"``, ...) or ``'destination'`` when called for
            matches in the destination attributes.
        logger: A logger object that can be used for log output.
        matches: The entries in the contact DB that matched the event
        organisations: The organisation associated with the matches
    """

    def __init__(self, event, section, base_logger):
        self._event = event
        self.section = section
        # base_logger should only be None for testing purposes.
        self.logger = (base_logger.getChild("script") if base_logger is not None
                       else None)
        self._matches, self._organisations = \
            contact_info_from_json(get_certbund_contacts(event, section))
        self._directives = []
        self.ensure_data_consistency()

    @property
    def matches(self):
        return self._matches

    @matches.setter
    def matches(self, value):
        self._matches = value
        self.ensure_data_consistency()

    @property
    def organisations(self):
        return self._organisations

    @organisations.setter
    def organisations(self, value):
        self._organisations = value
        self.ensure_data_consistency()

    def ensure_data_consistency(self):
        """Make sure data-structures stay consistent.
        In particular the links between matches and organisations need
        to stay sane if scripts modify this information.

        Scripts should not call this method directly! It wouldn't hurt,
        but it should not be necessary. This method is automatically
        called when new values are assigned to the matches or
        organisations attributes and by the rule bot between scripts.

        This method performs these cleanups:

         - rebuild internal dictionaries that speed up lookups

         - remove any references from matches to organisations that no
           longer exist

         - removes matches which are not associated to an organisation
           anymore, for instance du to scripts which changed the context.
           This does also remove the information about annotations and
           inhibitions from the context. This is a safe operation, as
           long as the scripts which care for inhibitions are executed
           before the context was altered.
        """
        # There are some more cleanups that might be useful but it's not
        # clear that they're a good idea and not doing them shouldn't be
        # a problem. In particular, possible cleanups are:
        #
        #
        # - remove organisations no longer referenced by a match object
        #   These can still be used to create directives, in cases where
        #   the information why an organisation matched is not
        #   important.

        self._organisation_map = {org.orgid: org
                                  for org in self.organisations}

        removematches = []
        # A list of matches which turned out to be empty (= w/o org.) and will be removed
        # from the matches

        for match in self.matches:
            match.organisations = [orgid
                                   for orgid in match.organisations
                                   if orgid in self._organisation_map]

            if not match.organisations:
                removematches.append(match)

        for m in removematches:
            # remove the empty matches
            self.matches.remove(m)

    def all_annotations(self):
        """Return an iterator over all annotations."""
        for item in self.organisations:
            for annotation in item.annotations:
                yield annotation
            for contact in item.contacts:
                for annotation in contact.annotations:
                    yield annotation
        for item in self.matches:
            for annotation in item.annotations:
                yield annotation

    def lookup_organisation(self, orgid):
        """Return the organisation with the given ID"""
        return self._organisation_map[orgid]

    def organisations_for_match(self, match):
        """Return the organisations associated with the match.
        The match objects themselves contain a list of organisation IDs.
        This method maps those IDs to the corresponding organisation
        objects.

        Args:
            match: A Match object

        Return: A list of Organisation instances
        """
        return [self.lookup_organisation(orgid)
                for orgid in match.organisations]

    def all_contacts(self):
        """Return an iterator over all contacts."""
        for org in self.organisations:
            for contact in org.contacts:
                yield contact

    @property
    def directives(self):
        """Return the directives that have been added to the context"""
        return self._directives

    def __getitem__(self, key):
        """Return the event's value for the key."""
        return self._event[key]

    def get(self, key):
        """Return the event's value for the key if it exists, None otherwise.
        """
        return self._event.get(key)

    def add_directive(self, directive):
        """Add the directive to the context."""
        self._directives.append(directive)

    def get_updated_event(self):
        """Return the event of the context with the directives added"""
        set_certbund_directives(self._event, self.section,
                                [d.as_dict_for_event(self._event)
                                 for d in self._directives])
        return self._event


def most_specific_matches(context):
    """Return the most specific matches from the context.

    Which matches are considered more specific depends on which
    attributes of the event matched and whether the matching entries in
    the contact database are manually managed or automatically.

    Returns:
        set of Match objects: The match objects which are considered
        most specific
    """
    by_field = defaultdict(lambda: {"manual": set(), "automatic": set()})

    for match in context.matches:
        by_field[match.field][match.managed].add(match)

    def get_preferred_by_field(field):
        if field not in by_field:
            return set()
        else:
            by_managed = by_field[field]
            return by_managed["manual"] or by_managed["automatic"]

    return (get_preferred_by_field("fqdn") |
            (get_preferred_by_field("ip") or get_preferred_by_field("asn")) |
            get_preferred_by_field("geolocation.cc"))


def keep_most_specific_contacts(context):
    """Modify context by removing all but the most specific matches.
    The most specific matches are determined with
    :py:func:`most_specific_matches`. All other matches are removed.

    Args:
        context (Context): the context used for rule scripts
    """
    orgids = set()
    matches = most_specific_matches(context)
    for match in matches:
        orgids |= set(match.organisations)
    for organisation in context.organisations:
        if organisation.orgid not in orgids:
            organisation.contacts = []


def notification_inhibited(context):
    """Return whether any inhibition annotation matches the context's event.

    This function iterates over all the annotations associated with the
    event's contact information (this includes the annotations of
    organisations, ASNs, FQDNs, networks, etc.) and if they're
    inhibition annotations -- i.e. if their tag is 'inhibition' --
    evaluations their condition. If any of these conditions evaluates to
    true, this function returns true.

    Args:
        context (Context): the context used for rule scripts

    Returns:
        bool: whether the condition of any inhibition annotation matched
    """
    return any(annotation.matches(context)
               for annotation in context.all_annotations()
               if annotation.tag == "inhibition")
