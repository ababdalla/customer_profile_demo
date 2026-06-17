import pandas as pd
import pyodbc

DSN_NAME = "IMPALA_PROD"


def get_connection():
    return pyodbc.connect(f"DSN={DSN_NAME};Trusted_Connection = yes;", autocommit=True)


def query_to_df(sql: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()
