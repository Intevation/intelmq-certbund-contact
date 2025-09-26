#!/usr/bin/python3
"""
Convert contact email addresses to lowercase

In the tables contact_automatic and contact, convert all values in the email column to lowercase.
"""
import psycopg2

def main():
    from contactdb_api.contactdb_api.serve import read_configuration
    conn = psycopg2.connect(dsn=read_configuration()["libpg conninfo"])
    try:
        with conn:
            for table in ('contact_automatic', 'contact'):
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE {table} SET email = lower(email) WHERE email ~ '[A-Z]'")
    finally:
        # Have to manually close connection even when using with-statement:
        # https://www.psycopg.org/docs/usage.html#with-statement
        conn.close()

if __name__ == '__main__':
    main()
