# Two expert bots to lookup contact information in a database and apply notification rules

Part of the [intelmq-cb-mailgen solution](https://github.com/Intevation/intelmq-mailgen-release).

An overview of the setup can be gained from the [IntelMQ Mailgen Docs](http://intevation.github.io/intelmq-mailgen/).

## Contact DB

### Automatic versus manual contacts

Two types of contacts are supported.
Both are modeled with a set of tables that differ
in the table name and in some columns.

#### 'Automatic' for externally maintained infos

The tables ending with `_automatic` shall hold contact
information that are maintained externally to the system.
They are designed so they can be updated or reimported
in a straight forward way. Several import sources are possible.

Therefore they have columns for `import_source` and `import_time`
in order to later decide which information to use. And there are
no fields for additional information as those information may potentially
get lost or be incorrect if the contents of the database changes
during an update or re-import.

The example for an external import source is contact data from RIPE,
please see [README-ripe-import.md](README-ripe-import.md).

#### 'Manual' to hold special cases

If the automatic contacts contain mistakes or a special case is needed,
the "manual" tables (that have no additional name suffix) can be used.
The information in the manual tables is to be considered the primary
source and maintained within this contact database.

Those special information shall be entered by regular users of the system
and should not interfere with the original external data. To keep the
system robust and consistent, there are no direct links
to the automatic tables.

To add special information to an already existing contact in the automatic
tables, all relevant tables entries of this specific automatic contact
have to be copied into the manual tables. The manual contact tables lack
columns about import source, but have comment and annotations
possibilities.

The comments are free-text fields that can be used to record additional
information that cannot not be expressed with the existing structured fields.
This allows for rare entries or to see what additional info people
would like to see in the database in future version of the database schema.

The annotations can be used as general "tags" to steer behaviour of
the system that can be configured on the level of administration rights,
but selected on the user level. The "simple" tags are designed to best be used
to denote a group of properties for sending behaviour that can be combined.
It is recommended to keep the number of tags low.
The tags have to be tuned after gaining experience in production use
and they will be easy to use if good tags are chosen over time.

The `inhibition`-annotations expose a generic way to prevent
sending out information based on field contents of the intelmq event
to users. Which is important if no administrator is available on short notice
or the behaviour is an exception that does not indicate a change in the general
behaviour groups. The `inhibition`-annotations are powerful
at the expense of being harder to use.


#### How to update external sources?
The manual entries have additional information to the automatic ones,
but also contain copied parts of the automatic entries.

If an automatic import source is updated, the additional
and copied information may be out of date and in need of change.

Example 1: the manual entry corrects a contact email address.
 With the next update, the email address in the RIPE database is
 updated to the correct one. Ideally the manual entry is deleted
 as it is not needed anymore. (Though it does not harm if is kept
 for a while.)

Example 2: again the manual entry corrects a contact email address.
  Now a network not is not served anymore by the same organisation coming
  with the RIPE database update. In this case the CIDR has to be removed
  from the manuel entry, because otherwise notifications will be send that
  should not go to the organisation anymore.

As there is no algorithmic way to know which info is better after an update
and thus which kind of changes have to be made,
a human has to involved.

At time of writing, this has to be done by an administrator, e.g once
a week or every two weeks for each import source, like:
 1. Check diffs if you would import for necessary changes.
 2. Stop the lookup expert-bot.
 3. Do the manual changes (e.g. with fody).
 4. Completely replace the automatic tables of this source with the new version.
 5. Restart the lookup bot.

For RIPE there is a script that will show the difference
between old and new automatic entries
and which manual entries are affected by these changes (see link
to the RIPE documentation above).


### Database Setup
Requires the python module psycopg2 (which is already installed if
you also use the postgresql-output bot).

Requires at least Postgresql v>=9.5 (compare to intelmq-fody-backend).

The following commands assume that PostgreSQL is running and listening on the
default port. They create a database called "contactdb" which matches the
default configuration of the bot.

```bash
su - postgres
createdb --encoding=UTF8 --template=template0 contactdb
psql -f /usr/share/intelmq-certbund-contact/sql/initdb.sql contactdb
```

A database user with the right to select the data in the Contact DB
must be created.  This is the account, which will be used in the bot's
configuration for accessing the database.

```bash
createuser intelmq --pwprompt
psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO intelmq;" contactdb
```

#### Adding default email tags

The names, values and default values for tags directly associated with
an email address have to be saved in the database.
(Maybe future version of fody-backend and fody will allow editing them, but
as of 2021-02-25 they don't.)

The following example adds two tag names with a few values:

```sql
INSERT INTO tag_name (tag_name, tag_name_order) VALUES ('Format', 1);
-- -> id 1
INSERT INTO tag_name (tag_name, tag_name_order) VALUES ('Constituency', 2);
-- -> id 2

COPY tag (tag_name_id, tag_value, tag_description, is_default) FROM STDIN
  WITH CSV;
1,CSV_inline,CSV inline,true
1,CSV_attachment,CSV attachment,false
2,network_operators,Network Operators,true
2,government,Government,false
2,CNI,Critical National Infrastructure,false
2,CNI_energy,CNI Energy,false
\.
```

(Tags for emails have been added with release 0.9.4 in 2019-05.)


### Schema Updates

When upgrading to new version take a look at
[NEWS.md](NEWS.md).

### Adding New Contacts

Contacts can be added to the database directly using SQL.
Though most users are expected to use a frontend application like Fody.

When put into the tables for manual contacts, the entries
will take precedence over contacts which
were imported automatically, i.e. by `ripe_import.py`.

Connect to the database:

```sh
  su - postgres
  psql contactdb

```
Add a contact:

```sql

-- 1. Prepare contact information

  \set asn 3320
  -- unique name of the organization:
  \set org_name 'org1'
  \set org_comment 'Example comment on organization.'
  \set contact_email 'test@example.com'
  \set contact_comment 'Test comment on contact.'
  -- set the notification interval in seconds
  -- an interval of -1 means no notifications will be generated
  \set notification_interval 0

-- 2. Add new contact

  BEGIN TRANSACTION;
  INSERT INTO autonomous_system (number) VALUES (:asn);
  WITH new_org AS (
    INSERT INTO organisation (name,comment)
    VALUES (:'org_name',:'org_comment')
    RETURNING id
  ),
  new_contact AS (
    INSERT INTO contact (email,format_id,comment)
    VALUES (:'contact_email', 2, :'contact_comment')
    RETURNING id
  ),
  new_ota AS (
    INSERT INTO organisation_to_asn (organisation_id,asn_id,notification_interval)
    VALUES (
      (SELECT id from new_org), :asn, :notification_interval
    )
  )
  INSERT INTO role (organisation_id,contact_id) VALUES (
      (SELECT id from new_org),
      (SELECT id from new_contact)
    )
  ;
  COMMIT TRANSACTION;

```

### Example change tags

If we call the simple text annotations tags, how could we change a tag
that has already be used?

Of course the notification rules may have to be changed
(see mailgen documentation) and possibly the list of known tags
that the fody-backend sends to fody.

For example the following sql command on database `contactdb`
change the tag  `whitelist-malware` to `Whitelist:Malware`:

```sql
BEGIN;

UPDATE autonomous_system_annotation
   SET annotation = '{"tag": "Whitelist:Malware"}'
 WHERE annotation ->> 'tag' = 'whitelist-malware';

UPDATE organisation_annotation
   SET annotation = '{"tag": "Whitelist:Malware"}'
 WHERE annotation ->> 'tag' = 'whitelist-malware';

UPDATE network_annotation
   SET annotation = '{"tag": "Whitelist:Malware"}'
 WHERE annotation ->> 'tag' = 'whitelist-malware';

UPDATE fqdn_annotation
   SET annotation = '{"tag": "Whitelist:Malware"}'
 WHERE annotation ->> 'tag' = 'whitelist-malware';

COMMIT;
```


## Suppress notification of contacts based upon certain criteria:

It is possible to suppress the notification of contacts based upon certain
criteria. Such can be: AS-number, IP addresses, FQDN, or Organisations.

To suppress notifications for such an Object, one has to create an annotation to
such an Object.

Remember: It's up to the `Rule Expert` to determine if such an annotation is
evaluated or not.

# Generating a graphic which visualizes the schema of the ContactDB

You can use `postgresql-autodoc` to do this. PG autodoc is available on both
debian and ubuntu via apt.

# Running the tests

Simply use pytest or `make tests`.
