"""
FitLife — Database Connection Manager
Handles SQL Server connections with pooling, retry logic, and health checks.
"""

import pyodbc
import json
import logging
import time
import threading
import sqlite3
import re
from pathlib import Path
from typing import Optional
from queue import Queue, Empty

logger = logging.getLogger(__name__)

# ─── Settings Loader ──────────────────────────────────────────────────────────
_settings_path = Path(__file__).parent.parent / "config" / "settings.json"

def _load_settings() -> dict:
    """Load database settings from config file."""
    try:
        with open(_settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.critical(f"settings.json not found at {_settings_path}")
        raise
    except json.JSONDecodeError as e:
        logger.critical(f"Invalid JSON in settings.json: {e}")
        raise


def _build_connection_string(db_cfg: dict) -> str:
    """Build the ODBC connection string from config dict."""
    driver = db_cfg.get("driver", "ODBC Driver 17 for SQL Server")
    server = db_cfg.get("server", "localhost")
    database = db_cfg.get("database", "FitLifeDB")
    timeout = db_cfg.get("connection_timeout", 30)
    trust_cert = db_cfg.get("trust_server_certificate", False)
    trust_part = "TrustServerCertificate=yes;" if trust_cert else ""

    if db_cfg.get("trusted_connection", True):
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"{trust_part}"
            f"Connection Timeout={timeout};"
        )
    else:
        username = db_cfg.get("username", "")
        password = db_cfg.get("password", "")
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"{trust_part}"
            f"Connection Timeout={timeout};"
        )


# ─── Connection Pool ──────────────────────────────────────────────────────────
class ConnectionPool:
    """Thread-safe SQL Server connection pool."""

    def __init__(self, connection_string: str, pool_size: int = 5, use_sqlite: bool = False):
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._all_connections: list = []
        self._initialized = False
        self._use_sqlite = use_sqlite

    def initialize(self):
        """Pre-populate the pool with connections."""
        try:
            for _ in range(self._pool_size):
                conn = self._create_connection()
                self._pool.put(conn)
                self._all_connections.append(conn)
            self._initialized = True
            logger.info(f"Connection pool initialized with {self._pool_size} connections.")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _create_connection(self):
        """Create a single new DB connection."""
        if self._use_sqlite:
            db_path = Path(__file__).parent / "fitlife.db"
            _init_sqlite_database(db_path)
            conn = create_sqlite_connection(db_path)
            return SQLiteConnectionWrapper(conn)
        else:
            conn = pyodbc.connect(self._connection_string, autocommit=False)
            conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
            conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-8")
            conn.setencoding(encoding="utf-8")
            return conn

    def get_connection(self, timeout: float = 10.0) -> pyodbc.Connection:
        """
        Acquire a connection from the pool.
        Returns a live connection, replacing dead ones automatically.
        """
        try:
            conn = self._pool.get(timeout=timeout)
            # Validate connection is still alive
            try:
                conn.execute("SELECT 1")
            except Exception:
                logger.warning("Dead connection detected, replacing...")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = self._create_connection()
            return conn
        except Empty:
            logger.warning("Connection pool exhausted, creating overflow connection.")
            return self._create_connection()

    def return_connection(self, conn: pyodbc.Connection):
        """Return a connection back to the pool."""
        try:
            if not self._pool.full():
                self._pool.put_nowait(conn)
            else:
                conn.close()
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")

    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
        logger.info("All pool connections closed.")


# ─── Global Pool Instance ─────────────────────────────────────────────────────
_pool: Optional[ConnectionPool] = None
_connection_string: Optional[str] = None
_use_sqlite = False


def translate_sql(sql: str) -> str:
    if not sql:
        return sql
    # Replace GETDATE() with CURRENT_TIMESTAMP
    sql = re.sub(r'(?i)\bGETDATE\(\)', 'CURRENT_TIMESTAMP', sql)
    # Replace CAST(GETDATE() AS DATE) with CURRENT_DATE
    sql = re.sub(r'(?i)\bCAST\s*\(\s*CURRENT_TIMESTAMP\s+AS\s+DATE\s*\)', 'CURRENT_DATE', sql)
    sql = re.sub(r'(?i)\bCAST\s*\(\s*GETDATE\(\)\s+AS\s+DATE\s*\)', 'CURRENT_DATE', sql)
    sql = re.sub(r'(?i)\bCAST\s*\(\s*GETUTCDATE\(\)\s+AS\s+DATE\s*\)', 'CURRENT_DATE', sql)
    # Replace DATEADD(day, X, Y) with sqlite_dateadd(X, Y)
    sql = re.sub(r'(?i)\bDATEADD\s*\(\s*day\s*,\s*(.*?)\s*,\s*(.*?)\)', r"sqlite_dateadd(\1, \2)", sql)
    # Replace DATEDIFF(day, X, Y) with sqlite_datediff(X, Y)
    sql = re.sub(r'(?i)\bDATEDIFF\s*\(\s*day\s*,\s*(.*?)\s*,\s*(.*?)\)', r"sqlite_datediff(\1, \2)", sql)

    # Translate SELECT TOP 1 or SELECT TOP (?) to LIMIT
    while True:
        match = re.search(r'(?i)\bSELECT\s+TOP\s+(\(\s*\?\s*\)|\?\b|\d+|\(\s*\d+\s*\))', sql)
        if not match:
            break
        
        top_idx = match.start()
        limit_val = match.group(1)
        
        # Check if this "SELECT TOP" is inside a parenthesized expression.
        open_paren_idx = -1
        paren_depth = 0
        for i in range(top_idx - 1, -1, -1):
            if sql[i] == '(':
                if paren_depth == 0:
                    open_paren_idx = i
                    break
                else:
                    paren_depth -= 1
            elif sql[i] == ')':
                paren_depth += 1
                
        if open_paren_idx != -1:
            close_paren_idx = -1
            paren_depth = 0
            for i in range(open_paren_idx + 1, len(sql)):
                if sql[i] == '(':
                    paren_depth += 1
                elif sql[i] == ')':
                    if paren_depth == 0:
                        close_paren_idx = i
                        break
                    else:
                        paren_depth -= 1
            
            if close_paren_idx != -1:
                sql = (
                    sql[:match.start()] + "SELECT" +
                    sql[match.end():close_paren_idx] + f" LIMIT {limit_val}" +
                    sql[close_paren_idx:]
                )
                continue
                
        sql = (
            sql[:match.start()] + "SELECT" +
            sql[match.end():] + f" LIMIT {limit_val}"
        )
        
    # Replace ISNULL(a, b) with coalesce(a, b)
    sql = re.sub(r'(?i)\bISNULL\s*\(', 'coalesce(', sql)
    
    return sql


class SQLiteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self._cursor = sqlite_cursor

    def execute(self, sql, params=()):
        translated_sql = translate_sql(sql)
        self._cursor.execute(translated_sql, params)
        return self

    def executemany(self, sql, params_list):
        translated_sql = translate_sql(sql)
        self._cursor.executemany(translated_sql, params_list)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class SQLiteConnectionWrapper:
    def __init__(self, sqlite_conn):
        self._conn = sqlite_conn

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def create_sqlite_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    def sqlite_dateadd(days, date_val):
        if date_val is None:
            return None
        from datetime import datetime, timedelta
        dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
            try:
                d_str = str(date_val).split(".")[0]
                dt = datetime.strptime(d_str, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            return date_val
        new_dt = dt + timedelta(days=int(days))
        return new_dt.strftime("%Y-%m-%d %H:%M:%S" if len(str(date_val)) > 10 else "%Y-%m-%d")
        
    conn.create_function("sqlite_dateadd", 2, sqlite_dateadd)
    
    def sqlite_datediff(start_date, end_date):
        if not start_date or not end_date:
            return None
        from datetime import datetime
        def parse_date(d_str):
            d_str = str(d_str).split(".")[0]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(d_str, fmt)
                except ValueError:
                    pass
            return None
        dt1 = parse_date(start_date)
        dt2 = parse_date(end_date)
        if dt1 and dt2:
            return (dt2 - dt1).days
        return None
        
    conn.create_function("sqlite_datediff", 2, sqlite_datediff)
    
    def sqlite_month(date_val):
        if not date_val:
            return None
        try:
            return int(str(date_val).split("-")[1])
        except Exception:
            return None
            
    conn.create_function("MONTH", 1, sqlite_month)
    
    def sqlite_year(date_val):
        if not date_val:
            return None
        try:
            return int(str(date_val).split("-")[0])
        except Exception:
            return None
            
    conn.create_function("YEAR", 1, sqlite_year)
    return conn


def _init_sqlite_database(db_path: Path):
    """Initialize SQLite database with schema and seed data if not present."""
    db_exists = db_path.exists()
    has_tables = False
    if db_exists:
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if c.fetchone():
                has_tables = True
            conn.close()
        except Exception:
            pass

    if not has_tables:
        logger.info(f"Initializing SQLite database at {db_path}...")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        schema_file = Path(__file__).parent / "schema_sqlite.sql"
        seed_file = Path(__file__).parent / "seed_data_sqlite.sql"
        if not schema_file.exists() or not seed_file.exists():
            logger.critical("SQLite schema or seed files are missing!")
            raise FileNotFoundError("schema_sqlite.sql or seed_data_sqlite.sql not found in database directory.")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            schema_sql = schema_file.read_text(encoding="utf-8")
            cursor.executescript(schema_sql)
            seed_sql = seed_file.read_text(encoding="utf-8")
            cursor.executescript(seed_sql)
            conn.commit()
            conn.close()
            logger.info("SQLite database initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize SQLite database: {e}")
            raise


def initialize_pool(max_retries: int = 3, retry_delay: float = 2.0):
    """
    Initialize the global connection pool with retry logic.
    Called once at application startup.
    """
    global _pool, _connection_string, _use_sqlite
    
    if _use_sqlite:
        try:
            logger.info("Initializing SQLite DB pool...")
            pool = ConnectionPool(connection_string="", pool_size=5, use_sqlite=True)
            pool.initialize()
            _pool = pool
            logger.info("SQLite database connection pool ready.")
            return True
        except Exception as e:
            logger.critical(f"Failed to initialize SQLite DB pool: {e}")
            return False

    settings = _load_settings()
    db_cfg = settings.get("database", {})
    _connection_string = _build_connection_string(db_cfg)
    pool_size = db_cfg.get("pool_size", 5)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Initializing DB pool (attempt {attempt}/{max_retries})...")
            pool = ConnectionPool(_connection_string, pool_size, use_sqlite=False)
            pool.initialize()
            _pool = pool
            logger.info("Database connection pool ready.")
            return True
        except Exception as e:
            logger.error(f"Pool init attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.critical("Failed to initialize database connection pool after all retries.")
    return False


def get_connection():
    """Get a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call initialize_pool() first.")
    return _pool.get_connection()


def return_connection(conn):
    """Return a connection to the pool."""
    if _pool is not None:
        _pool.return_connection(conn)


def close_pool():
    """Close all connections — call at app shutdown."""
    global _pool
    if _pool:
        _pool.close_all()
        _pool = None


def test_connection(max_retries: int = 3, retry_delay: float = 2.0) -> bool:
    """
    Test database connectivity without using the pool.
    Used for the startup check and connection error screen.
    """
    global _use_sqlite
    
    try:
        settings = _load_settings()
        db_cfg = settings.get("database", {})
        conn_str = _build_connection_string(db_cfg)
    except Exception as e:
        logger.error(f"Failed to load settings: {e}. Falling back to SQLite...")
        _use_sqlite = True
        return True

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Testing MS SQL Server connection (attempt {attempt}/{max_retries})...")
            conn = pyodbc.connect(conn_str, timeout=3)
            conn.close()
            logger.info("MS SQL Server connection test successful.")
            _use_sqlite = False
            return True
        except Exception as e:
            logger.warning(f"MS SQL Server test attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.warning("MS SQL Server connection failed. Falling back to SQLite...")
    _use_sqlite = True
    try:
        db_path = Path(__file__).parent / "fitlife.db"
        _init_sqlite_database(db_path)
        conn = create_sqlite_connection(db_path)
        conn.close()
        logger.info("SQLite connection fallback test successful.")
        return True
    except Exception as e:
        logger.error(f"SQLite connection fallback test failed: {e}")
        return False


# ─── Context Manager for Safe Query Execution ─────────────────────────────────
class DatabaseConnection:
    """
    Context manager for database operations.
    Usage:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(...)
            conn.commit()
    """

    def __init__(self):
        self.conn: Optional[pyodbc.Connection] = None
        self.cursor: Optional[pyodbc.Cursor] = None

    def __enter__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            try:
                if self.conn:
                    self.conn.rollback()
            except Exception:
                pass
            logger.error(f"DB transaction rolled back due to: {exc_val}")
        else:
            try:
                if self.conn:
                    self.conn.commit()
            except Exception as e:
                logger.error(f"Error committing transaction: {e}")
        try:
            if self.cursor:
                self.cursor.close()
        except Exception:
            pass
        if self.conn:
            return_connection(self.conn)
        return False  # Don't suppress exceptions


def execute_query(sql: str, params: tuple = (), fetch: str = "all"):
    """
    Execute a parameterized query and return results.

    Args:
        sql: SQL query string with ? placeholders
        params: Tuple of parameters
        fetch: "all", "one", or "none"

    Returns:
        List of rows, single row, or None
    """
    with DatabaseConnection() as (conn, cursor):
        cursor.execute(sql, params)
        if fetch == "all":
            return cursor.fetchall()
        elif fetch == "one":
            return cursor.fetchone()
        elif fetch == "none":
            return cursor.rowcount
    return None


def execute_many(sql: str, params_list: list):
    """Execute a parameterized query for multiple rows."""
    with DatabaseConnection() as (conn, cursor):
        cursor.executemany(sql, params_list)
        return cursor.rowcount


def get_connection_info() -> dict:
    """Return current DB connection info (safe, no passwords)."""
    global _use_sqlite
    if _use_sqlite:
        return {
            "server": "SQLite Fallback",
            "database": "fitlife.db",
            "driver": "sqlite3",
            "trusted_connection": True,
        }
    try:
        settings = _load_settings()
        db_cfg = settings.get("database", {})
        return {
            "server": db_cfg.get("server", ""),
            "database": db_cfg.get("database", ""),
            "driver": db_cfg.get("driver", ""),
            "trusted_connection": db_cfg.get("trusted_connection", True),
        }
    except Exception:
        return {}
