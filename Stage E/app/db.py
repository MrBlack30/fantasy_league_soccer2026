"""
db.py - PostgreSQL access layer for the Fantasy League Manager GUI.

Wraps psycopg2 with a small, focused API used by the rest of the app:
  * connect / close / is_connected
  * fetch        -> (columns, rows) for any SELECT
  * execute      -> rowcount for INSERT / UPDATE / DELETE (+ captured NOTICEs)
  * call_function_table / call_refcursor / call_procedure  -> Stage D programs

All statements use parameter binding (%s) so the app is safe from SQL injection
and handles types (dates, numerics) correctly.
"""

import psycopg2
import psycopg2.extras


# Default connection settings - the Stage D database (Docker container my_postgres).
DEFAULT_SETTINGS = {
    "host": "localhost",
    "port": "5432",
    "dbname": "mydatabase",
    "user": "myuser",
    "password": "mypassword",
}


class DatabaseError(Exception):
    """Friendly wrapper around any psycopg2 error so the UI can show one message."""


class Database:
    def __init__(self):
        self.conn = None
        self.settings = dict(DEFAULT_SETTINGS)

    # ----------------------------------------------------------------- connect
    def connect(self, host, port, dbname, user, password):
        """Open a connection. Raises DatabaseError on failure."""
        try:
            self.close()
            self.conn = psycopg2.connect(
                host=host,
                port=int(port),
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=6,
            )
            # We manage transactions ourselves (needed for REF CURSOR functions).
            self.conn.autocommit = False
            self.settings = {
                "host": host, "port": str(port), "dbname": dbname,
                "user": user, "password": password,
            }
        except Exception as exc:  # noqa: BLE001 - re-raise as friendly error
            self.conn = None
            raise DatabaseError(str(exc).strip()) from exc

    def is_connected(self):
        return self.conn is not None and self.conn.closed == 0

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:  # noqa: BLE001
                pass
            self.conn = None

    # ------------------------------------------------------------------- read
    def fetch(self, sql, params=None):
        """Run a SELECT and return (columns, rows). rows is a list of tuples."""
        self._require_conn()
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params or ())
                cols = [d.name for d in cur.description] if cur.description else []
                rows = cur.fetchall()
            self.conn.commit()
            return cols, rows
        except Exception as exc:  # noqa: BLE001
            self._rollback()
            raise DatabaseError(str(exc).strip()) from exc

    def fetch_one(self, sql, params=None):
        cols, rows = self.fetch(sql, params)
        return cols, (rows[0] if rows else None)

    def scalar(self, sql, params=None):
        _, row = self.fetch_one(sql, params)
        return row[0] if row else None

    # ------------------------------------------------------------------ write
    def execute(self, sql, params=None):
        """Run an INSERT/UPDATE/DELETE. Returns (rowcount, notices)."""
        self._require_conn()
        try:
            del self.conn.notices[:]
            with self.conn.cursor() as cur:
                cur.execute(sql, params or ())
                count = cur.rowcount
            self.conn.commit()
            return count, self._drain_notices()
        except Exception as exc:  # noqa: BLE001
            self._rollback()
            raise DatabaseError(str(exc).strip()) from exc

    # -------------------------------------------------- Stage D program calls
    def call_function_table(self, sql, params=None):
        """Call a set-returning function: SELECT * FROM fn(...). Returns (cols, rows)."""
        return self.fetch(sql, params)

    def call_refcursor(self, select_sql, cursor_name, params=None):
        """
        Call a function that returns a REF CURSOR, then FETCH ALL from it.
        Must run inside one transaction (autocommit is off).
        Returns (cols, rows, notices).
        """
        self._require_conn()
        try:
            del self.conn.notices[:]
            with self.conn.cursor() as cur:
                cur.execute(select_sql, params or ())          # opens the cursor
                returned = cur.fetchone()[0]                   # cursor name
                name = returned or cursor_name
                cur.execute('FETCH ALL FROM "%s"' % name)
                cols = [d.name for d in cur.description] if cur.description else []
                rows = cur.fetchall()
            self.conn.commit()
            return cols, rows, self._drain_notices()
        except Exception as exc:  # noqa: BLE001
            self._rollback()
            raise DatabaseError(str(exc).strip()) from exc

    def call_procedure(self, call_sql, params=None):
        """CALL a stored procedure. Returns the list of NOTICE messages it raised."""
        self._require_conn()
        try:
            del self.conn.notices[:]
            with self.conn.cursor() as cur:
                cur.execute(call_sql, params or ())
            self.conn.commit()
            return self._drain_notices()
        except Exception as exc:  # noqa: BLE001
            self._rollback()
            raise DatabaseError(str(exc).strip()) from exc

    # --------------------------------------------------------------- internals
    def _require_conn(self):
        if not self.is_connected():
            raise DatabaseError("Not connected to the database.")

    def _rollback(self):
        try:
            if self.conn is not None:
                self.conn.rollback()
        except Exception:  # noqa: BLE001
            pass

    def _drain_notices(self):
        notices = [n.strip() for n in self.conn.notices]
        del self.conn.notices[:]
        return notices
