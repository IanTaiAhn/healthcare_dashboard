"""
SQLite storage layer with revision tracking.

Each FRED pull is stored with a fetch timestamp so revisions can be detected
and model retraining is reproducible against historical data snapshots.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "workforce.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH):
    """Create tables if they don't exist."""
    conn = get_connection(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS series_observations (
            series_id TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (series_id, date, fetched_at)
        );

        CREATE INDEX IF NOT EXISTS idx_series_date
            ON series_observations (series_id, date);

        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            observation_count INTEGER,
            latest_date TEXT,
            status TEXT DEFAULT 'ok'
        );
        """
    )
    conn.close()


def store_series(series_id: str, data: pd.Series, db_path: Path = DEFAULT_DB_PATH):
    """
    Store a FRED series pull with current timestamp for revision tracking.
    """
    conn = get_connection(db_path)
    now = datetime.utcnow().isoformat()

    records = [
        (series_id, date.strftime("%Y-%m-%d"), float(val), now)
        for date, val in data.items()
        if pd.notna(val)
    ]

    conn.executemany(
        "INSERT OR REPLACE INTO series_observations (series_id, date, value, fetched_at) "
        "VALUES (?, ?, ?, ?)",
        records,
    )

    conn.execute(
        "INSERT INTO fetch_log (series_id, fetched_at, observation_count, latest_date) "
        "VALUES (?, ?, ?, ?)",
        (
            series_id,
            now,
            len(records),
            data.dropna().index.max().strftime("%Y-%m-%d") if len(data.dropna()) > 0 else None,
        ),
    )
    conn.commit()
    conn.close()


def load_series(series_id: str, db_path: Path = DEFAULT_DB_PATH) -> pd.Series:
    """
    Load the latest version of a series from the database.
    Uses the most recent fetched_at for each date.
    """
    conn = get_connection(db_path)
    query = """
        SELECT date, value
        FROM series_observations
        WHERE series_id = ?
          AND fetched_at = (
              SELECT MAX(fetched_at) FROM series_observations WHERE series_id = ?
          )
        ORDER BY date
    """
    df = pd.read_sql_query(query, conn, params=(series_id, series_id))
    conn.close()

    if df.empty:
        return pd.Series(dtype=float)

    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["value"]


def get_fetch_history(series_id: str, db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Return the fetch log for a given series — useful for detecting revisions."""
    conn = get_connection(db_path)
    df = pd.read_sql_query(
        "SELECT * FROM fetch_log WHERE series_id = ? ORDER BY fetched_at DESC",
        conn,
        params=(series_id,),
    )
    conn.close()
    return df
