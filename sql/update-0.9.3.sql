CREATE INDEX network_automatic_cidr_gist_idx ON network_automatic
       USING gist (address inet_ops);
