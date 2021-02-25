#!/usr/bin/env python3
"""Create email tag example cases from a list of email addresses.

The convention is that email addresses in the db have been changed
by prepending an 'x-', so they differ from what the current ripe files have.
We call them emailA.

When run with ripe_diff the emails coming from the ripe files would be
imported, thus new, we call them emailB.

Precondition: At least we have tag_id 1 and 2 in the db.

We skip safety checks and ignore style as this is for development. :)
"""
import fileinput

def emailB(f):
    return f.readline().rstrip('\n')

def emailA(f):
    return 'x-' + emailB(f)

db_lines = []

with fileinput.input() as f:
    # case 1: both addresses have no tags, we do nothing
    f.readline()

    # case 2.1.1: emailA is disabled, emailB not
    db_lines.append("INSERT INTO email_status (email, enabled) VALUES ('{}','{}');".format(emailA(f), "false"))

    # case 2.1.2: emailA has a tag, emailB not
    db_lines.append("INSERT INTO email_tag (email, tag_id) VALUES ('{}','{}');".format(emailA(f), 1))

    # TODO

for db_line in db_lines:
    print(db_line)
