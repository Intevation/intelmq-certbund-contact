"""
Choose the most relevant contacts

Prefer CIDR over ASN matches
Prefer special constituency tags over others

Do some debug output
"""

from collections import defaultdict
import ipaddress


CONSTITUENCY_TAGS = {
    "TargetGroup:Administration",
    "TargetGroup:ISP",
    "TargetGroup:Energy",
    "TargetGroup:Finance",
    "TargetGroup:Military",
    }


def constituency_organisations(organisations):
    """Return those organisations that belonging to the primary target group.

    These are all organisations that have contacts which have tags
    contained in CONSTITUENCY_TAGS. Contacts that do not have such a tag
    are removed from those organisations.
    """
    primaries = []
    for org in organisations:
        restricted_contacts = []
        for contact in org.contacts:
            for annotation in contact.annotations:
                if annotation.tag in CONSTITUENCY_TAGS:
                    restricted_contacts.append(contact)
                    break

        if restricted_contacts:
            org.contacts = restricted_contacts
            primaries.append(org)

    return primaries


class MatchSelector:

    """Allow easy access to a set of matches by matched field"""

    def __init__(self, matches):
        self.by_field = defaultdict(lambda: {"manual": set(),
                                             "automatic": set()})

        for match in matches:
            self.by_field[match.field][match.managed].add(match)

    def get_preferred_by_field(self, field):
        """Get the preferred matches for the given field.

        If both manuallly and automatically managed matches are present,
        only the manually managed matches are returned.
        """
        if field not in self.by_field:
            return set()
        else:
            by_managed = self.by_field[field]
            return by_managed["manual"] or by_managed["automatic"]

    def manual_AS_matches(self):
        return self.by_field["asn"]["manual"]

    def get_preferred_ip_matches(self, context, reference_org):
        manual_matches = self.by_field["ip"]["manual"]
        if manual_matches:
            return set(manual_matches)

        reference_addresses = set(contact.email
                                  for contact in reference_org.contacts)

        for match in self.by_field["ip"]["automatic"]:
            for org in context.organisations_for_match(match):
                if (set(contact.email for contact in org.contacts)
                    & reference_addresses):
                    continue
        result.add(match)
        return result


def most_specific_cidr_matches(matches):
    by_mask_len = defaultdict(list)
    for match in matches:
        by_mask_len[ipaddress.ip_network(match.address).prefixlen].append(match)
    sorted_by_mask_len = sorted(by_mask_len.items())
    if sorted_by_mask_len:
        return sorted_by_mask_len[-1][-1]
    else:
        return []


def match_recipients(context, match):
    """Return the addresses of all contacts for the given match."""
    return set(contact.email
               for org in context.organisations_for_match(match)
               for contact in org.contacts)


def interesting_cidr_matches(context, selector):
    """Return a set with the 'interesting' CIDR matches.

    The interesting CIDR matches those automatic CIDR matches that do
    not share a recipient address with an automatic AS match.
    """
    asn_recipients = set(address
                         for match in selector.by_field["asn"]["automatic"]
                         for address in match_recipients(context, match))
    return set(match
               for match in most_specific_cidr_matches(
                   selector.by_field["ip"]["automatic"])
               if not asn_recipients & match_recipients(context, match))


def determine_directives(context):
    context.logger.debug("============= 20prioritize_contacts.py ===========")

    constituency_orgs = constituency_organisations(context.organisations)
    if constituency_orgs:
        context.logger.debug("At least one Constituency organisation detected, removing all others.")
        context.organisations = constituency_orgs

    selector = MatchSelector(context.matches)

    preferred_as_matches = selector.get_preferred_by_field("asn")
    preferred_ip_matches = (selector.by_field["ip"]["manual"]
                            or interesting_cidr_matches(context, selector))

    # preferring CIDR over AS
    matches = preferred_ip_matches or preferred_as_matches

    if not constituency_orgs:
        matches |= selector.get_preferred_by_field("geolocation.cc")

    org_ids = set(i for match in matches for i in match.organisations)
    context.matches = list(matches)
    context.organisations = [org for org in context.organisations
                             if org.orgid in org_ids]

    context.logger.debug("Content of the Context AFTER this script:")
    context.logger.debug("Organisations: %r", context.organisations)
    context.logger.debug("Matches: %r", context.matches)

    return None
