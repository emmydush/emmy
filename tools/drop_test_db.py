import psycopg2
import sys

DBNAME = "test_ims_db"
HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "Jesuslove@12"

try:
    conn = psycopg2.connect(
        dbname="postgres", user=USER, password=PASSWORD, host=HOST, port=PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid();",
        (DBNAME,),
    )
    cur.execute(f"DROP DATABASE IF EXISTS {DBNAME};")
    print("Dropped test database:", DBNAME)
    cur.close()
    conn.close()
except Exception as e:
    print("Error dropping test database:", e)
    sys.exit(1)
