"""
Adds additional internal contacts to events based on the Constituency (Target group)

Copyright (C) 2024-2025 by Bundesamt für Sicherheit in der Informationstechnik
Software engineering by Intevation GmbH
"""

from copy import deepcopy
from collections import defaultdict

from intelmq_certbund_contact.rulesupport import Organisation, Contact, Match, most_specific_matches
from intelmq_certbund_contact.annotations import Annotation, Const
from ruleshelper import get_contact_group


CONSTITUENCIES = {
    "network_operators":
        Organisation(name='Copy Network Operators', orgid=-1, managed='manual', sector=None, import_source='21constituency_copies.py',
                     contacts=[Contact(email='gov@cert.example', managed='manual', email_status='enabled',
                                       annotations=[Annotation('Format:CSV_inline', condition=Const(True)),
                                                    Annotation('Constituency:network_operators', condition=Const(True))])],
                     annotations=[]),
    "Finance":
        Organisation(name='Copy Government', orgid=-1, managed='manual', sector=None, import_source='21constituency_copies.py',
                     contacts=[Contact(email='finance@cert.example', managed='manual', email_status='enabled',
                                       annotations=[Annotation('Format:CSV_inline', condition=Const(True)),
                                                    Annotation('Constituency:government', condition=Const(True))])],
                     annotations=[]),
#    "CNI": ...,
#    "CNI_energy": ...,
    }


def copy_match(source_match: Match, organisation_id: int):
    return Match(field=source_match.field, managed='manual',
                 organisations=[organisation_id],
                 annotations=source_match.annotations,
                 address=source_match.address)


def find_match_by_orgid(matches, orgid):
    for index, match in enumerate(matches):
        if orgid in match.organisations:
            return index


def determine_directives(context):
    context.logger.debug("============= 21constituency_contacts.py ===========")

    # Iterate over all contacts and check if they are in a constituency contact group. If they are, save the organisation id
    # Multiple organisations can be in the same constituency
    contact_groups = defaultdict(set)
    for organisation in context.organisations:
        for contact in organisation.contacts:
            contact_group = get_contact_group(contact)
            # Return value None means no Contact Group is detected
            if contact_group:
                context.logger.debug('Detected Contact Group %r in organisation %r. Internal contact for this groups does %sexist.', contact_group, organisation.orgid, '' if contact_group in CONSTITUENCIES else 'not ')
                context.logger.debug(f'Already in: {organisation.orgid in contact_groups[contact_group]}')
                if contact_group in CONSTITUENCIES:
                    contact_groups[contact_group].add(organisation.orgid)
            else:
                context.logger.debug('Detected no Contact Group in organisation %r', organisation.orgid)

    # shortcut if nothing to do:
    if not contact_groups:
        return None
    else:
        context.logger.debug(f'Contact Groups: {contact_groups}')

    # Get the highest existing organisation id, so we can use consecutive number afterwards
    max_orgid = max(org.orgid for org in context.organisations)

    counter = 1
    for contact_group, organisation_ids in contact_groups.items():
        for organisation_id in organisation_ids:
            # The matches must reference the organisation id, and all organisations must be referenced by a match, as ensure_data_consistency otherwise deletes them
            # context.ensure_data_consistency is called when setting organisations or matches, but not when we only modify the existing objects.
            # ensure_data_consistency will be called at the end by the expert itself, so consistency is ensured
            context.organisations.append(deepcopy(CONSTITUENCIES[contact_group]))
            # set the new organisation id to a the next available ID
            context.organisations[-1].orgid = max_orgid + counter
            # Add the new organisation to the existing match
            context.matches[find_match_by_orgid(context.matches, organisation_id)].organisations.append(max_orgid + counter)
            counter += 1

    context.logger.debug("Content of the Context AFTER this script:")
    context.logger.debug("Organisations: %r", context.organisations)
    context.logger.debug("Matches: %r", context.matches)

