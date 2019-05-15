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
