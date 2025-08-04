"""Remove invalid contact information.

Invalid contact information are:

 - organisations that have no associated contacts at all

 - contacts with an empty email address or email address marked disabled

When this script finishes, all remaining matches in the context are
associated with organisations that have at least one contact and all
contacts have a non-empty email address.
"""


def determine_directives(context):
    context.logger.debug("============= 03remove-invalid.py ===========")
    valid_organisations = []
    context.logger.debug("All matches: %r", context.matches)
    for org in context.organisations:
        org.contacts = [contact for contact in org.contacts
                        if contact.email and contact.email_status == "enabled" ]
        if org.contacts:
            valid_organisations.append(org)
    context.organisations = valid_organisations
