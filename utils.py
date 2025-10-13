import psycopg2
import pandas as pd

USER_NAME = 'rubicon'
DB = 'sleepdb'
CONNECTION_STRING = f'postgresql+psycopg2://{USER_NAME}@localhost:5432/{DB}'

def create_conn(db):
    # Connect and Collect
    conn = psycopg2.connect(
        host="localhost"
        , user="rubicon"
        , connect_timeout=1
        , password=""
        , database=db)

    return conn

def table_exists(db, table_name, schema_name='public'):
    """
    Checks if a table exists in the specified schema of the PostgreSQL database.

    Args:
        conn: A psycopg2 connection object.
        table_name: The name of the table to check.
        schema_name: The name of the schema where the table is expected (default is 'public').

    Returns:
        True if the table exists, False otherwise.
    """
    conn = create_conn(db)
    with conn.cursor() as cur:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            );
        """
        cur.execute(query, (schema_name, table_name))
        return cur.fetchone()[0]

def retrieve_query(query):
    conn = create_conn(DB)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    column_names = [i[0] for i in cursor.description]
    df = pd.DataFrame(data, columns=column_names)
    conn.close()

    # decode binary data
    for el in df:
        if type(df[el][0]) == bytearray:
            df[el] = df[el].apply(lambda el: el.decode('utf-8') if el is not None else el)

    return df