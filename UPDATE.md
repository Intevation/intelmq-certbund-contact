# Update instructions

When upgrading the intelmq-certbund-contact package sometimes
additional manual steps are needed.  These are documented here.

If installing from scratch, please refer to README.md for the
necessary steps.

## Update to 1.2.0

This version adds RIPE routing information to a `route_automatic` table, only used by Tuency.
See https://github.com/Intevation/intelmq-certbund-contact/pull/23

Use [`sql/update-1.2.0.sql`](sql/update-1.2.0.sql) to create the table and index.

## Update to 0.9.4

The Version 0.9.4 implements new email associated tags.  For them the
database must be updated according to the section **Email Tags** in
[db-updates-sql.md](sql/db-updates-sql.md).


Then, tag (group) names can be added using statements like:

```
  INSERT INTO tag_name (tag_name, tag_name_order)
    VALUES ('Format', 1);
```
and actual tags like:
```
  INSERT INTO tag (tag_name_id, tag_value,
                   tag_description, is_default)
    VALUES (1, 'csv_inline', 'CSV inline', true);
  INSERT INTO tag (tag_name_id, tag_value,
                   tag_description, is_default)
    VALUES (1, 'csv_attachment', 'CSV attachment', false);
```

## update to previous versions
See [db-updates-sql.md](sql/db-updates-sql.md).


