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

def emailB(line):
    if not line:
        raise EOFError("not enough email addresses")
    return line.rstrip('\n')

def emailA(line):
    return 'x-' + emailB(line)

db_lines = []

with fileinput.input() as f:
    # case 1: both addresses have no tags, we do nothing
    db_lines.append("-- leaving '{}' alone".format(emailA(f.readline())))

    # case 2.1.1: emailA is disabled, emailB not
    db_lines.append("INSERT INTO email_status (email, enabled) VALUES ('{}','{}');".format(emailA(f.readline()), "false"))

    # case 2.1.2: emailA has a tag, emailB not
    db_lines.append("INSERT INTO email_tag (email, tag_id) VALUES ('{}','{}');".format(emailA(f.readline()), 1))

    # case 3.1: emailA is enabled (no entry), emailB is disabled
    db_lines.append("INSERT INTO email_status (email, enabled) VALUES ('{}','{}');".format(emailB(f.readline()), "false"))

    # case 3.2: emailA has no tag, emailB has a tag
    db_lines.append("INSERT INTO email_tag (email, tag_id) VALUES ('{}','{}');".format(emailB(f.readline()), 1))

    # case 4.1: both are disabled
    line = f.readline()
    db_lines.append("INSERT INTO email_status (email, enabled) VALUES ('{}','{}');".format(emailA(line), "false"))
    db_lines.append("INSERT INTO email_status (email, enabled) VALUES ('{}','{}');".format(emailB(line), "false"))

    # case 4.2: both have a tag
    line = f.readline()
    db_lines.append("INSERT INTO email_tag (email, tag_id) VALUES ('{}','{}');".format(emailA(line), 1))
    db_lines.append("INSERT INTO email_tag (email, tag_id) VALUES ('{}','{}');".format(emailB(line), 1))

for db_line in db_lines:
    print(db_line)
