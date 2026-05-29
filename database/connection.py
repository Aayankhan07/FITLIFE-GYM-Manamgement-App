"""
FitLife — Database Connection Manager
Handles SQL Server connections with pooling, retry logic, and health checks.
"""

import pyodbc
import json
import logging
import time
import threading
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

    def __init__(self, connection_string: str, pool_size: int = 5):
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._all_connections: list = []
        self._initialized = False

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

    def _create_connection(self) -> pyodbc.Connection:
        """Create a single new DB connection."""
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


def initialize_pool(max_retries: int = 3, retry_delay: float = 2.0):
    """
    Initialize the global connection pool with retry logic.
    Called once at application startup.
    """
    global _pool, _connection_string
    settings = _load_settings()
    db_cfg = settings.get("database", {})
    _connection_string = _build_connection_string(db_cfg)
    pool_size = db_cfg.get("pool_size", 5)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Initializing DB pool (attempt {attempt}/{max_retries})...")
            pool = ConnectionPool(_connection_string, pool_size)
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


def get_connection() -> pyodbc.Connection:
    """Get a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call initialize_pool() first.")
    return _pool.get_connection()


def return_connection(conn: pyodbc.Connection):
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
    settings = _load_settings()
    db_cfg = settings.get("database", {})
    conn_str = _build_connection_string(db_cfg)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Testing DB connection (attempt {attempt}/{max_retries})...")
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            logger.info("Database connection test successful.")
            return True
        except pyodbc.Error as e:
            logger.warning(f"DB test attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error("Database connection test failed after all retries.")
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
