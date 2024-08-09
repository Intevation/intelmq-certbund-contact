# Upgrade-Instructions for the Contact Database

This file contains instructions for upgrading the contact database.

## Fody Audit Log (1.0.3)

#### upgrade

```sh
  su - postgres
  psql \
    -f /usr/share/doc/intelmq-certbund-contact/sql/update-1.0.3.sql \
    contactdb
```

Thereafter the access rights must be granted like:
```sql
  GRANT SELECT, INSERT, UPDATE, DELETE ON public.audit_log TO apiuser;
  GRANT ALL ON public.audit_log_log_id_seq TO apiuser;
```

## Email Tags (0.9.4)

#### upgrade

```sh
  su - postgres
  psql \
    -f /usr/share/doc/intelmq-certbund-contact/sql/update-0.9.4.sql \
    contactdb
```

Thereafter the access rights must be adjusted like:
```sql
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO intelmq;
  GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public TO contacts;
```

#### downgrade
```sql
DROP FUNCTION email_annotations(VARCHAR(100));
DROP VIEW email_annotation;
DROP TABLE email_tag;
DROP TABLE tag;
DROP TABLE tag_name;
```

## Update to 0.9.3

The Version 0.9.3 of intelmq-certbund-contact relies on features of
PostgreSQL 9.4 to accelerate operations on inet addresses.  Therefor
an additional index must be created in the database, this is done by
the provided update script:

```sh
  su - postgres
  psql \
    -f /usr/share/doc/intelmq-certbund-contact/sql/update-0.9.3.sql \
    contactdb
```


## Instructions for old versions

The instructions below only apply to database that were created before
the code was maintained in the intelmq-certbund-contact repository.

### New Table `email_status`

#### upgrade
```sql
CREATE TABLE email_status (
    email VARCHAR(100) PRIMARY KEY,
    enabled BOOLEAN NOT NULL,
    added TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Make sure the user used by the contact bot can access the table.
-- Adapt the username if necessary.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO intelmq;
```

#### downgrade
```sql
DROP TABLE email_status;
```


### Indices for the asn column on the organisation_to_asn tables

#### upgrade
```sql
CREATE INDEX organisation_to_asn_asn_idx
    ON organisation_to_asn (asn);
CREATE INDEX organisation_to_asn_automatic_asn_idx
    ON organisation_to_asn_automatic (asn);
```

#### downgrade
```sql
DROP INDEX organisation_to_asn_asn_idx;
DROP INDEX organisation_to_asn_automatic_asn_idx;
```


### Add FQDN index again

This index was implicitly removed by the removal of the UNIQUE
constraint on fqdn (fqdn). The analogous index on network (address) is
not needed currently and therefore it's not a problem that it was
removed together the UNIQUE constraint.


#### upgrade
```sql
CREATE INDEX fqdn_fqdn_idx ON fqdn (fqdn);
```


#### downgrade
```sql
DROP INDEX fqdn_fqdn_idx;
```


### Enabling multiple entries for fqdn and network

#### upgrade

```sql
ALTER TABLE fqdn DROP CONSTRAINT fqdn_fqdn_key;
ALTER TABLE network DROP CONSTRAINT network_address_key;
```

#### downgrade
```sql
ALTER TABLE fqdn ADD CONSTRAINT fqdn_fqdn_key UNIQUE (fqdn);
ALTER TABLE network ADD  CONSTRAINT network_address_key UNIQUE (address);
```


### Intevation/intelmq/issues/17 (certbund-contact: renaming pgp_key_id)

#### upgrade
```sql
-- you may need to close other connections/cursors to the db before
ALTER TABLE contact RENAME COLUMN pgp_key_id TO openpgp_fpr;
ALTER TABLE contact_automatic RENAME COLUMN pgp_key_id TO openpgp_fpr;
```

#### downgrade
```sql
-- you may need to close other connections/cursors to the db before
ALTER TABLE contact RENAME COLUMN openpgp_fpr TO pgp_key_id;
ALTER TABLE contact_automatic RENAME COLUMN openpgp_fpr TO pgp_key_id;
```

