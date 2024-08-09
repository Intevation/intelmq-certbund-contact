BEGIN;

CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    time TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    "table" VARCHAR(50) NOT NULL,
    "user" TEXT NOT NULL,
    operation VARCHAR(20) NOT NULL,
    object_type TEXT NOT NULL,
    object_value TEXT NOT NULL,
    "before" JSONB,
    "after" JSONB
);

ALTER TABLE organisation_annotation
    ALTER COLUMN annotation SET DATA TYPE jsonb;

ALTER TABLE autonomous_system_annotation
    ALTER COLUMN annotation SET DATA TYPE jsonb;

ALTER TABLE network_annotation
    ALTER COLUMN annotation SET DATA TYPE jsonb;

ALTER TABLE fqdn_annotation
    ALTER COLUMN annotation SET DATA TYPE jsonb;

-- Type change from JSON to JSONB
CREATE OR REPLACE FUNCTION email_annotations(email_address VARCHAR(100))
RETURNS JSONB AS
$$
DECLARE
    annotations JSONB;
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
RETURN coalesce(annotations, '[]'::JSONB);
END;
$$ LANGUAGE plpgsql STABLE;

COMMIT;
