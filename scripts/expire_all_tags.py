#!/usr/bin/python3
"""
Add an expiry date to all existing annotations matching "Whitelist:" (can be changed)
All annotations of an organisation expire at the same day
The expire dates are spread over a configurable time window

Run the tests with, for example,
pytest scripts/expire_all_tags.py
"""
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter
register_adapter(dict, Json)

START_DATE = datetime.now().date() + timedelta(days=30)
TIME_STEP = timedelta(days=7)
MAXIMUM_STEPS = 20
VERBOSE = True
DRY_RUN = True
TAG_PATTERN = 'Whitelist:%'


def test_distribute_orgas_over_time():
    assert distribute_orgas_over_time(list(range(4)), 1) == [[0, 1, 2, 3]]
    assert distribute_orgas_over_time(list(range(4)), 6) == [[0], [1], [2], [3]]
    assert distribute_orgas_over_time(list(range(4)), 3) == [[0, 1], [2, ], [3, ]]
    assert distribute_orgas_over_time([3, 5, 10, 14, 20, 50, 1001], 3) == [[3, 5, 10], [14, 20], [50, 1001]]


def distribute_orgas_over_time(org_ids: list, number_of_steps: int):
    if number_of_steps > len(org_ids):  # more steps than needed, cut off
        number_of_steps = len(org_ids)
    org_ids = org_ids.copy()  # make sure we have type list, and a copy of it to modify it
    per_step = len(org_ids) // number_of_steps
    residue = len(org_ids) % number_of_steps
    result = []
    for step in range(number_of_steps):
        result.append([])
        for org_id in range(per_step):
            result[-1].append(org_ids.pop(0))
        if step == 0:  # in first batch, add the residue
            for org_id in range(residue):
                result[-1].append(org_ids.pop(0))
    return result


def test_time_iterator():
    assert list(time_iterator(datetime(2024, 1, 1).date(), timedelta(days=1), [[1]])) == [('2024-01-01', [1])]
    assert list(time_iterator(datetime(2024, 1, 1).date(), timedelta(days=3), [[3, 5, 10], [14, 20], [50, 1001]])) == \
        [('2024-01-01', [3, 5, 10]), ('2024-01-04', [14, 20]), ('2024-01-07', [50, 1001])]


def time_iterator(start: datetime, time_step: timedelta, org_steps: list):
    time = start
    for org_step in org_steps:
        yield time.isoformat(), org_step
        time = time + time_step


def get_all_affected_organisations(cur):
    cur.execute("""
        SELECT DISTINCT organisation_id FROM (
        SELECT 'org' AS anno_type, organisation_id, annotation from organisation_annotation WHERE annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL
        UNION SELECT  'network' AS anno_type, organisation_id, annotation FROM network_annotation NATURAL JOIN organisation_to_network WHERE annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL
        UNION SELECT 'asn' AS anno_type, organisation_id, annotation FROM autonomous_system_annotation NATURAL JOIN organisation_to_asn WHERE annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL
        UNION SELECT 'fqdn' AS anno_type, organisation_id, annotation FROM fqdn_annotation NATURAL JOIN organisation_to_fqdn WHERE annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL
        ) AS all_annos
        WHERE annotation ->> 'tag' LIKE %s AND (annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL)
        ORDER BY organisation_id""",
        (TAG_PATTERN, ) )
    return cur.fetchall()


COMMON_WHERE = "WHERE organisation_id = %s AND annotation ->> 'tag' LIKE %s AND (annotation ->> 'expires' = '' OR annotation ->> 'expires' IS NULL)"


def main():
    from contactdb_api.contactdb_api.serve import read_configuration
    with psycopg2.connect(dsn=read_configuration()["libpg conninfo"]) as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        affected = get_all_affected_organisations(cur)
        print(f"Retrieved {len(affected)} organisations with unexpired tags matching {TAG_PATTERN!r}")
        affected_org_ids = [row['organisation_id'] for row in affected]
        distributed_orgas = distribute_orgas_over_time(affected_org_ids, MAXIMUM_STEPS)
        for date, org_ids in time_iterator(START_DATE, TIME_STEP, distributed_orgas):
            print(f'Batch {date}: {org_ids}')
            for org_id in org_ids:
                if VERBOSE:
                    print(f'Processing Organisation ID {org_id}')
                # ORGANISATION ANNOTATIONS
                cur.execute(f"SELECT organisation_annotation_id, annotation FROM organisation_annotation {COMMON_WHERE}", (org_id, TAG_PATTERN, ))
                for result in cur.fetchall():
                    new_annotation = result['annotation']
                    new_annotation['expires'] = date
                    if VERBOSE:
                        print(cur.mogrify("UPDATE organisation_annotation SET annotation = %s WHERE organisation_annotation_id = %s",
                                          (new_annotation,
                                           result['organisation_annotation_id'])).decode())
                    if not DRY_RUN:
                        cur.execute("UPDATE organisation_annotation SET annotation = %s WHERE organisation_annotation_id = %s",
                                    (new_annotation,
                                     result['organisation_annotation_id']))
                # NETWORK ANNOTATIONS
                cur.execute(f"SELECT network_annotation_id, annotation FROM network_annotation JOIN organisation_to_network USING (network_id) {COMMON_WHERE}", (org_id, TAG_PATTERN, ))
                for result in cur.fetchall():
                    new_annotation = result['annotation']
                    new_annotation['expires'] = date
                    if VERBOSE:
                        print(cur.mogrify("UPDATE network_annotation SET annotation = %s WHERE network_annotation_id = %s",
                                          (new_annotation,
                                           result['network_annotation_id'])).decode())
                    if not DRY_RUN:
                        cur.execute("UPDATE network_annotation SET annotation = %s WHERE network_annotation_id = %s",
                                    (new_annotation,
                                     result['network_annotation_id']))
                # AS ANNOTATIONS
                cur.execute(f"SELECT autonomous_system_annotation_id, annotation FROM autonomous_system_annotation JOIN organisation_to_asn USING (asn) {COMMON_WHERE}", (org_id, TAG_PATTERN, ))
                for result in cur.fetchall():
                    new_annotation = result['annotation']
                    new_annotation['expires'] = date
                    if VERBOSE:
                        print(cur.mogrify("UPDATE autonomous_system_annotation SET annotation = %s WHERE autonomous_system_annotation_id = %s",
                                          (new_annotation,
                                           result['autonomous_system_annotation_id'])).decode())
                    if not DRY_RUN:
                        cur.execute("UPDATE autonomous_system_annotation SET annotation = %s WHERE autonomous_system_annotation_id = %s",
                                    (new_annotation,
                                     result['autonomous_system_annotation_id']))
                # DOMAIN ANNOTATIONS
                cur.execute(f"SELECT fqdn_annotation_id, annotation FROM fqdn_annotation JOIN organisation_to_fqdn USING (fqdn_id) {COMMON_WHERE}", (org_id, TAG_PATTERN, ))
                for result in cur.fetchall():
                    new_annotation = result['annotation']
                    new_annotation['expires'] = date
                    if VERBOSE:
                        print(cur.mogrify("UPDATE fqdn_annotation SET annotation = %s WHERE fqdn_annotation_id = %s",
                                          (new_annotation,
                                           result['fqdn_annotation_id'])).decode())
                    if not DRY_RUN:
                        cur.execute("UPDATE fqdn_annotation SET annotation = %s WHERE fqdn_annotation_id = %s",
                                    (new_annotation,
                                     result['fqdn_annotation_id']))


if __name__ == '__main__':
    main()
