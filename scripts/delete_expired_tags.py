#!/usr/bin/python3
"""
Add an expiry date to all existing annotations matching "Whitelist:" (can be changed)
All annotations of an organisation expire at the same day
The expire dates are spread over a configurable time window

Run the tests with, for example,
pytest scripts/expire_all_tags.py
"""
import argparse
import psycopg2
from datetime import datetime
from textwrap import dedent
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter
register_adapter(dict, Json)

SQL_GET_EXPIRED_ANNOTATIONS = """
    SELECT {table}_annotation_id, {index}, annotation FROM {table}_annotation
    WHERE (annotation ->> 'expires')::date < {timespec} %s AND annotation ->> 'expires' IS NOT NULL AND annotation ->> 'expires' != ''""".replace('\n    ', ' ')
SQL_DELETE_ANNOTATION = """
    DELETE FROM {table}_annotation
    WHERE {table}_annotation_id = %s""".replace('\n    ', ' ')
SQL_AUDIT_LOG = """
    INSERT INTO audit_log
    ("table", "user", operation, object_type, object_value, "before")
    VALUES
    (%s, %s, %s, %s, %s, %s)""".replace('\n    ', ' ')
DEFAULT_AUDIT_LOG_USER = '_system_expired_cleanup'


TABLE_TO_NAME_COLUMN = {
    'organisation': 'name',
    'fqdn': 'fqdn',
    'network': 'address',
}
TABLE_TO_INDEX = {
    'autonomous_system': 'asn',
    'fqdn': 'fqdn_id',
    'network': 'network_id',
    'organisation': 'organisation_id',
}


def _get_name_to_object(object_type: str, object_value: int, cur) -> str:
    if object_type == 'autonomous_system':
        return object_value
    cur.execute("""SELECT {0} FROM {1} WHERE {1}_id = %s""".format(TABLE_TO_NAME_COLUMN[object_type], object_type),
                (object_value, ))
    return cur.fetchall()[0][0]


def main():
    parser = argparse.ArgumentParser('delete_expired_tags',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=dedent('''
        Setting the age to 2025-07-07 deletes all tags that are expired on 2025-07-06 or earlier, but not the tags that expire on 2025-07-07 itself.
        Setting the age to '0 days' on 2025-07-08 deletes all tags that are expired, on 2025-07-07 or earlier.
        Setting the age to '1 day' on 2025-07-08 deletes all tags that are expired before 2025-07-07: on 2025-07-06 or earlier.
        '''))
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('age', help="Either a Postgres-parseable date interval, for example '1 month' or an absolute date, formatted %%Y-%%m-%%d '2020-01-01'.")
    parser.add_argument('-u', '--audit-log-user', default=DEFAULT_AUDIT_LOG_USER,
                        help=f'The username to appear in the audit log for deleting the expired annotations. Default: {DEFAULT_AUDIT_LOG_USER}')
    args = parser.parse_args()

    try:  # Test if the age is an absolute date
        datetime.strptime(args.age, '%Y-%m-%d')
    except ValueError:  # no it's not absolute -> relative
        time_is_relative = True
    else:
        time_is_relative = False
    if args.verbose:
        print(f'Given time specifier is relative: {time_is_relative}')

    from contactdb_api.contactdb_api.serve import read_configuration
    with psycopg2.connect(dsn=read_configuration()["libpg conninfo"]) as conn:
        with conn.cursor() as cur:
            for table in ('organisation', 'autonomous_system', 'network', 'fqdn'):
                print(f'Processing {table}_annotation')
                select_query = SQL_GET_EXPIRED_ANNOTATIONS.format(table=table, index=TABLE_TO_INDEX[table], timespec='CURRENT_DATE - INTERVAL' if time_is_relative else '')
                if args.verbose >= 2:
                    print(cur.mogrify(select_query, (args.age, )).decode())
                cur.execute(select_query, (args.age, ))
                for expired_anno in cur.fetchall():
                    anno_id, foreign_id, annotation = expired_anno
                    if args.verbose:
                        print(f'Deleting expired {table} (ID {foreign_id}) annotation {annotation!r}, ID {anno_id}')
                    if args.verbose >= 2:
                        print(cur.mogrify(SQL_DELETE_ANNOTATION.format(table=table), (anno_id, )).decode())
                        print(cur.mogrify(SQL_AUDIT_LOG.format(table=table),
                                          (f'{table}_annotation', args.audit_log_user, 'remove', table, _get_name_to_object(table, foreign_id, cur=cur), annotation)).decode())
                    if not args.dry_run:
                        cur.execute(SQL_DELETE_ANNOTATION.format(table=table), (anno_id, ))
                        cur.execute(SQL_AUDIT_LOG.format(table=table),
                                    (f'{table}_annotation', args.audit_log_user, 'remove', table, _get_name_to_object(table, foreign_id, cur=cur), annotation))


if __name__ == '__main__':
    main()
