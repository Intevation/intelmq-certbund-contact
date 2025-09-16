#!/usr/bin/python3
"""
Convert contact email addresses to lowercase

In the tables contact_automatic and contact, convert all values in the email column to lowercase.
"""
import psycopg2

_CURSOR_NAME = 'email_lowercase_cursor'

def main():
    from contactdb_api.contactdb_api.serve import read_configuration
    conn = psycopg2.connect(dsn=read_configuration()["libpg conninfo"])
    try:
        with conn:
            # https://stackoverflow.com/a/67729179
            with conn.cursor() as update_cur:
                for table in ('contact_automatic', 'contact'):
                    with conn.cursor(name=_CURSOR_NAME) as select_cur:
                        select_cur.itersize = 1
                        select_cur.execute(f'SELECT email FROM {table} FOR UPDATE')
                        for email, in select_cur:
                            email_lower = email.encode().lower().decode()
                            if email != email_lower:
                                update_cur.execute(f'UPDATE {table} SET email = %s WHERE CURRENT OF {_CURSOR_NAME}', (email_lower,))
    finally:
        # Have to manually close connection even when using with-statement:
        # https://www.psycopg.org/docs/usage.html#with-statement
        conn.close()

if __name__ == '__main__':
    main()
