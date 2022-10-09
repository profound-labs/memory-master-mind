#!/usr/bin/env python3

import sqlite3
import contextlib
from memory_master_mind import DB_PATH

def create_challenge_settings_table() -> None:
    query = """
        CREATE TABLE IF NOT EXISTS
            challenge_settings(
                id integer primary key autoincrement,
                challenge VARCHAR UNIQUE not null,
                settings_json VARCHAR not null
            );
    """

    with contextlib.closing(sqlite3.connect(DB_PATH)) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(query)
            connection.commit()

def save_settings(challenge: str, settings_json: str) -> bool:
    if get_settings(challenge):
        query = """
            UPDATE challenge_settings
            SET settings_json = ?
            WHERE challenge = ?;
        """
    else:
        query = """
            INSERT INTO challenge_settings
              (settings_json, challenge)
            VALUES (?, ?);
        """

    try:
        with contextlib.closing(sqlite3.connect(DB_PATH)) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                cursor.execute(query, (settings_json, challenge))
                connection.commit()
        return True
    except Exception as e:
        print(str(e))
        return False

def get_settings(challenge: str):
    result = ""
    select_query = """
        SELECT * FROM challenge_settings
        WHERE challenge = ?;
    """
    with contextlib.closing(sqlite3.connect(DB_PATH)) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(select_query, (challenge,))
            connection.commit()
            result = cursor.fetchone()
    # (1, 'numbers', 'cool')
    return result

def db_init():
    if not DB_PATH.exists():
        create_challenge_settings_table()
