from psycopg2 import pool

# Initialize the connection pool
conn_pool = pool.SimpleConnectionPool(
    1,  # minimum number of connections
    10, # maximum number of connections
    host="localhost",
    dbname="wallet",
    port=5432,
    user="postgres",
    password="Nick2708!",
)

def get_conn():
    return conn_pool.getconn()

def put_conn(conn):
    conn_pool.putconn(conn)
