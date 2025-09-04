-- Update script for the route_automatic table.

CREATE TABLE route_automatic (
    route_automatic_id SERIAL PRIMARY KEY,
    address CIDR NOT NULL,
    asn BIGINT NOT NULL,
    import_source VARCHAR(500) NOT NULL,
    import_time TIMESTAMP NOT NULL,

    -- explicitly name the constraint to make sure it has the same name
    -- as the constraint created by initdb.sql.
    CONSTRAINT automatic_templ_import_source_check CHECK (import_source <> ''),

    UNIQUE (address, asn, import_source)
);

CREATE INDEX route_automatic_cidr_gist_idx ON route_automatic
       USING gist (address inet_ops);
