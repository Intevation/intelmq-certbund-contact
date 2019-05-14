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
CREATE TABLE tag_name (
    tag_name_id SERIAL PRIMARY KEY,
    tag_name TEXT NOT NULL,
    tag_name_order INTEGER NOT NULL,

    UNIQUE (tag_name)
);

CREATE TABLE tag (
    tag_id SERIAL PRIMARY KEY,
    tag_name_id INTEGER NOT NULL,
    tag_value TEXT NOT NULL,
    tag_description TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,

    UNIQUE (tag_name_id, tag_value),
    FOREIGN KEY (tag_name_id) REFERENCES tag_name (tag_name_id)
);

CREATE UNIQUE INDEX tag_unique_default_tags_idx
    ON tag (tag_name_id)
 WHERE is_default;


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
            json_build_object('tag', tag_name || ':' || tag_value)
       FROM email_tag
       JOIN tag USING (tag_id)
       JOIN tag_name USING (tag_name_id);


CREATE OR REPLACE FUNCTION email_annotations(email_address VARCHAR(100))
RETURNS JSON AS
$$
DECLARE
    annotations JSON;
BEGIN
WITH
  email_tags (tag_name_id, annotation)
    AS (SELECT tag_name_id,
               json_build_object('tag',
                                 tag_name.tag_name || ':' || tag.tag_value)
               AS annotation
          FROM email_tag
          JOIN tag USING (tag_id)
          JOIN tag_name USING (tag_name_id)
         WHERE email_tag.email = email_address),
  default_tags (tag_name_id, default_tag)
    AS (SELECT tag_name_id,
               MIN(tag_name.tag_name || ':' || tag.tag_value)
               FILTER (WHERE is_default)
               AS default_tag
          FROM tag JOIN tag_name USING (tag_name_id)
      GROUP BY tag_name_id),
  default_annotations (tag_name_id, default_annotation)
    AS (SELECT tag_name_id,
               CASE WHEN default_tag IS NULL THEN NULL
                    ELSE json_build_object('tag', default_tag)
               END AS default_annotation
         FROM default_tags)
SELECT json_agg(COALESCE(annotation, default_annotation))
       FILTER (WHERE COALESCE(annotation, default_annotation) IS NOT NULL)
       INTO annotations
  FROM email_tags RIGHT OUTER JOIN default_annotations USING (tag_name_id);

RETURN coalesce(annotations, '[]'::JSON);
END;
$$ LANGUAGE plpgsql STABLE;
```

#### downgrade
```sql
DROP FUNCTION email_annotations(VARCHAR(100));
DROP VIEW email_annotation;
DROP TABLE email_tag;
DROP TABLE tag;
DROP TABLE tag_name;
```
