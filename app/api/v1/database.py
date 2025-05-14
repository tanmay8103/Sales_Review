import sqlite3
from sqlite3 import Row
from typing import Any

def get_db():
    conn = sqlite3.connect('sales_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)} 