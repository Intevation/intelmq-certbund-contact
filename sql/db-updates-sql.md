# Upgrade-Instructions for the Contact Database

This file contains instructions for upgrading the contact database.


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

### Email Tags

#### upgrade
```sql
CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL,

    UNIQUE (category_name)
);


CREATE TABLE tag (
    tag_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    tag_description TEXT NOT NULL,

    UNIQUE (category_id, tag_name),
    FOREIGN KEY (category_id) REFERENCES category (category_id)
);


CREATE TABLE email_tag (
    email VARCHAR(100) NOT NULL,
    tag_id INTEGER NOT NULL,

    PRIMARY KEY (email, tag_id),

    FOREIGN KEY (tag_id) REFERENCES tag (tag_id)
);

CREATE INDEX email_tag_email_idx
          ON email_tag (email);


CREATE VIEW email_annotation (email, annotation)
  AS SELECT email,
            json_build_object('tag', category_name || ':' || tag_name)
       FROM email_tag
       JOIN tag USING (tag_id)
       JOIN category USING (category_id);
```

#### downgrade
```sql
DROP VIEW email_annotation;
DROP TABLE email_tag;
DROP TABLE tag;
DROP TABLE category;
```
