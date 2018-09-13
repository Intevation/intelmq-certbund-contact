# Update instructions

When upgrading the intelmq-certbund-contact package sometimes
additional manual steps are needed.  These are documented here.

If installing from scratch, please refer to README.md for the
necessary steps.

## Update to 0.9.3

The Version 0.9.3 of intelmq-certbund-contact relies on features of
PostgreSQL 9.4 to accelerate operations on inet addresses.  Therefor
an additional index must be creates in the database, this is done by
the provided update script:

```
    su - postgres
    psql \
      -f /usr/share/doc/intelmq-certbund-contact/sql/update-0.9.3.sql \
      contactdb
```
