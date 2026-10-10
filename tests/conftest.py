import os
import sqlite3
import pytest
from models.user import User
from database.connection import test_connection, initialize_pool

TEST_DB_PATH = "database/test_fitlife.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Sets up a temporary SQLite database and initializes connection pool for unit testing."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    con = sqlite3.connect(TEST_DB_PATH)
    schema_path = os.path.join("database", "schema_sqlite.sql")
    seed_path = os.path.join("database", "seed_data_sqlite.sql")

    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
    
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())

    con.close()

    # Initialize connection pool (fallback to SQLite)
    test_connection()
    try:
        initialize_pool()
    except Exception:
        pass

    yield TEST_DB_PATH

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass
