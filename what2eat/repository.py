"""SQLite persistence with explicit transactions and immutable history snapshots."""

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from .colors import option_color
from .dates import month_bounds
from .models import FoodOption, LunchRecord

SCHEMA_VERSION = 1


class LunchRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path) if str(path) != ":memory:" else None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), timeout=5, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._initialize()
        except Exception:
            self.connection.close()
            raise

    def _initialize(self) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, SCHEMA_VERSION):
            raise sqlite3.DatabaseError("数据文件版本不兼容，请使用相应版本的程序。")
        with self.transaction():
            self.connection.execute(
                """CREATE TABLE IF NOT EXISTS options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    name_key TEXT NOT NULL,
                    weight REAL NOT NULL CHECK(weight >= 0 AND weight <= 1.000000000001),
                    color TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                    CHECK(active = 0 OR weight > 0)
                )"""
            )
            self.connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS active_option_names "
                "ON options(name_key) WHERE active = 1"
            )
            self.connection.execute(
                """CREATE TABLE IF NOT EXISTS lunches (
                    day TEXT PRIMARY KEY,
                    option_id INTEGER NOT NULL REFERENCES options(id),
                    option_name TEXT NOT NULL,
                    color TEXT NOT NULL,
                    rerolls INTEGER NOT NULL CHECK(rerolls BETWEEN 0 AND 3),
                    chosen_at TEXT NOT NULL
                )"""
            )
            self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Lock before reading, so another process cannot evade the reroll limit."""
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            raise

    def options(self) -> list[FoodOption]:
        rows = self.connection.execute(
            "SELECT id, name, weight, color FROM options WHERE active = 1 ORDER BY id"
        )
        return [FoodOption(row["id"], row["name"], row["weight"], row["color"]) for row in rows]

    def insert_option(self, name: str, weight: float) -> int:
        cursor = self.connection.execute(
            "INSERT INTO options(name, name_key, weight, color) VALUES (?, ?, ?, ?)",
            (name, name.casefold(), weight, "#000000"),
        )
        option_id = int(cursor.lastrowid)
        self.connection.execute(
            "UPDATE options SET color = ? WHERE id = ?", (option_color(option_id), option_id)
        )
        return option_id

    def update_weights(self, option_ids: Sequence[int], weights: Sequence[float]) -> None:
        if len(option_ids) != len(weights):
            raise ValueError("Option IDs and weights must have the same length")
        self.connection.executemany(
            "UPDATE options SET weight = ? WHERE id = ? AND active = 1",
            [(weight, option_id) for option_id, weight in zip(option_ids, weights)],
        )

    def deactivate(self, option_ids: Sequence[int]) -> None:
        self.connection.executemany(
            "UPDATE options SET active = 0, weight = 0 WHERE id = ?",
            [(option_id,) for option_id in option_ids],
        )

    @staticmethod
    def _record(row: sqlite3.Row) -> LunchRecord:
        return LunchRecord(
            date.fromisoformat(row["day"]), row["option_id"], row["option_name"],
            row["color"], row["rerolls"], datetime.fromisoformat(row["chosen_at"]),
        )

    def record(self, day: date) -> LunchRecord | None:
        row = self.connection.execute("SELECT * FROM lunches WHERE day = ?", (day.isoformat(),)).fetchone()
        return self._record(row) if row is not None else None

    def history_before(self, day: date) -> list[LunchRecord]:
        rows = self.connection.execute(
            "SELECT * FROM lunches WHERE day < ? ORDER BY day", (day.isoformat(),)
        )
        return [self._record(row) for row in rows]

    def month(self, year: int, month: int) -> list[LunchRecord]:
        start, end = month_bounds(year, month)
        rows = self.connection.execute(
            "SELECT * FROM lunches WHERE day >= ? AND day < ? ORDER BY day",
            (start.isoformat(), end.isoformat()),
        )
        return [self._record(row) for row in rows]

    def save_record(self, record: LunchRecord) -> None:
        self.connection.execute(
            """INSERT INTO lunches(day, option_id, option_name, color, rerolls, chosen_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(day) DO UPDATE SET
                 option_id = excluded.option_id, option_name = excluded.option_name,
                 color = excluded.color, rerolls = excluded.rerolls,
                 chosen_at = excluded.chosen_at""",
            (record.day.isoformat(), record.option_id, record.option_name,
             record.color, record.rerolls, record.chosen_at.isoformat()),
        )

    def close(self) -> None:
        self.connection.close()
