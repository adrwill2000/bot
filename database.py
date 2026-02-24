"""
database.py — SQLite persistence layer for the Call Channel Roast Bot.

Tables:
  users              — global user registry
  groups             — every chat/group the bot has been used in
  calls              — all calls, tagged with chat_id
  user_stats         — global lifetime stats per user
  group_user_stats   — per-group stats per user (for group leaderboards)
"""

import json
import sqlite3
from typing import Dict, List, Optional


class Database:
    def __init__(self, path: str = "calls.db"):
        self.path = path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ─────────────────────────────────────────────────────────────────
    # SCHEMA
    # ─────────────────────────────────────────────────────────────────
    def init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT    DEFAULT '',
                    first_name  TEXT    DEFAULT 'Anon',
                    created_at  TEXT    DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS groups (
                    chat_id         INTEGER PRIMARY KEY,
                    title           TEXT    DEFAULT 'Unknown Group',
                    username        TEXT    DEFAULT '',
                    chat_type       TEXT    DEFAULT 'group',
                    is_active       INTEGER DEFAULT 1,
                    registered_at   TEXT    DEFAULT (datetime('now')),
                    registered_by   INTEGER,
                    settings        TEXT    DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS calls (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    chat_id         INTEGER NOT NULL DEFAULT 0,
                    coin            TEXT    NOT NULL,
                    entry_price     REAL    NOT NULL,
                    exit_price      REAL,
                    target          REAL,
                    stop_loss       REAL,
                    pnl_pct         REAL,
                    is_duplicate    INTEGER DEFAULT 0,
                    duplicate_of    INTEGER,
                    spike_alerted   INTEGER DEFAULT 0,
                    status          TEXT    DEFAULT 'open',
                    created_at      TEXT    DEFAULT (datetime('now')),
                    closed_at       TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id      INTEGER PRIMARY KEY,
                    total_calls  INTEGER DEFAULT 0,
                    closed_calls INTEGER DEFAULT 0,
                    wins         INTEGER DEFAULT 0,
                    losses       INTEGER DEFAULT 0,
                    total_pnl    REAL    DEFAULT 0.0,
                    avg_pnl      REAL    DEFAULT 0.0,
                    best_call    REAL    DEFAULT 0.0,
                    worst_call   REAL    DEFAULT 0.0,
                    duplicates   INTEGER DEFAULT 0,
                    got_copied   INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS group_user_stats (
                    chat_id      INTEGER NOT NULL,
                    user_id      INTEGER NOT NULL,
                    total_calls  INTEGER DEFAULT 0,
                    closed_calls INTEGER DEFAULT 0,
                    wins         INTEGER DEFAULT 0,
                    losses       INTEGER DEFAULT 0,
                    total_pnl    REAL    DEFAULT 0.0,
                    avg_pnl      REAL    DEFAULT 0.0,
                    best_call    REAL    DEFAULT 0.0,
                    worst_call   REAL    DEFAULT 0.0,
                    duplicates   INTEGER DEFAULT 0,
                    got_copied   INTEGER DEFAULT 0,
                    PRIMARY KEY (chat_id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_calls_coin_status
                    ON calls(coin, status);
                CREATE INDEX IF NOT EXISTS idx_calls_user_status
                    ON calls(user_id, status);
                CREATE INDEX IF NOT EXISTS idx_calls_chat_id
                    ON calls(chat_id);
                CREATE INDEX IF NOT EXISTS idx_calls_closed_at
                    ON calls(closed_at);
                CREATE INDEX IF NOT EXISTS idx_gus_chat
                    ON group_user_stats(chat_id);
            """)
        self._migrate()

    def _migrate(self):
        """Safe column-level migrations for existing databases."""
        with self._conn() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(calls)").fetchall()]
            if "chat_id" not in cols:
                conn.execute("ALTER TABLE calls ADD COLUMN chat_id INTEGER DEFAULT 0")

    # ─────────────────────────────────────────────────────────────────
    # USERS
    # ─────────────────────────────────────────────────────────────────
    def upsert_user(self, user_id: int, username: str, first_name: str):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username   = excluded.username,
                    first_name = excluded.first_name
            """, (user_id, username or "", first_name or "Anon"))
            conn.execute(
                "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,)
            )

    def get_user(self, user_id: int) -> Dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else {
                "user_id": user_id, "username": "", "first_name": "Mystery Trader"
            }

    # ─────────────────────────────────────────────────────────────────
    # GROUPS
    # ─────────────────────────────────────────────────────────────────
    def upsert_group(self, chat_id: int, title: str, username: str,
                     chat_type: str, registered_by: int):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO groups (chat_id, title, username, chat_type, registered_by)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    title     = excluded.title,
                    username  = excluded.username,
                    is_active = 1
            """, (chat_id, title or "Unknown", username or "", chat_type, registered_by))

    def get_group(self, chat_id: int) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM groups WHERE chat_id = ?", (chat_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_active_groups(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM groups WHERE is_active = 1 ORDER BY registered_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_group_settings(self, chat_id: int) -> Dict:
        group = self.get_group(chat_id)
        if not group:
            return {}
        try:
            return json.loads(group.get("settings") or "{}")
        except Exception:
            return {}

    def update_group_settings(self, chat_id: int, settings: Dict):
        with self._conn() as conn:
            conn.execute(
                "UPDATE groups SET settings = ? WHERE chat_id = ?",
                (json.dumps(settings), chat_id)
            )

    def get_group_count(self) -> int:
        with self._conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM groups WHERE is_active = 1"
            ).fetchone()[0]

    # ─────────────────────────────────────────────────────────────────
    # CALLS
    # ─────────────────────────────────────────────────────────────────
    def insert_call(self, user_id: int, coin: str, entry_price: float,
                    target: Optional[float] = None, stop_loss: Optional[float] = None,
                    is_duplicate: int = 0, duplicate_of: Optional[int] = None,
                    chat_id: int = 0) -> int:
        with self._conn() as conn:
            cur = conn.execute("""
                INSERT INTO calls (user_id, chat_id, coin, entry_price, target,
                                   stop_loss, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, coin.upper(), entry_price,
                  target, stop_loss, is_duplicate, duplicate_of))
            call_id = cur.lastrowid
            conn.execute("""
                INSERT INTO user_stats (user_id, total_calls) VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET total_calls = total_calls + 1
            """, (user_id,))
            if chat_id:
                conn.execute("""
                    INSERT INTO group_user_stats (chat_id, user_id, total_calls)
                    VALUES (?, ?, 1)
                    ON CONFLICT(chat_id, user_id) DO UPDATE
                    SET total_calls = total_calls + 1
                """, (chat_id, user_id))
            return call_id

    def get_call(self, call_id: int) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM calls WHERE id = ?", (call_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_open_call_for_coin(self, coin: str, chat_id: int = 0) -> Optional[Dict]:
        with self._conn() as conn:
            if chat_id:
                row = conn.execute("""
                    SELECT * FROM calls
                    WHERE coin = ? AND chat_id = ? AND status = 'open' AND is_duplicate = 0
                    ORDER BY created_at ASC LIMIT 1
                """, (coin.upper(), chat_id)).fetchone()
            else:
                row = conn.execute("""
                    SELECT * FROM calls
                    WHERE coin = ? AND status = 'open' AND is_duplicate = 0
                    ORDER BY created_at ASC LIMIT 1
                """, (coin.upper(),)).fetchone()
            return dict(row) if row else None

    def get_user_open_call(self, user_id: int, coin: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT * FROM calls
                WHERE user_id = ? AND coin = ? AND status = 'open'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, coin.upper())).fetchone()
            return dict(row) if row else None

    def get_all_open_calls(self, chat_id: int = 0) -> List[Dict]:
        with self._conn() as conn:
            if chat_id:
                rows = conn.execute("""
                    SELECT * FROM calls WHERE status = 'open' AND chat_id = ?
                    ORDER BY created_at DESC
                """, (chat_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM calls WHERE status = 'open' ORDER BY created_at DESC
                """).fetchall()
            return [dict(r) for r in rows]

    def get_open_calls_for_monitoring(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM calls
                WHERE status = 'open' AND is_duplicate = 0 AND spike_alerted = 0
            """).fetchall()
            return [dict(r) for r in rows]

    def close_call(self, call_id: int, exit_price: float, pnl_pct: float):
        with self._conn() as conn:
            conn.execute("""
                UPDATE calls
                SET status='closed', exit_price=?, pnl_pct=?, closed_at=datetime('now')
                WHERE id=?
            """, (exit_price, pnl_pct, call_id))
            row = conn.execute(
                "SELECT user_id, chat_id FROM calls WHERE id=?", (call_id,)
            ).fetchone()
            if row:
                self._update_pnl_stats_conn(conn, row["user_id"], row["chat_id"], pnl_pct)

    def _update_pnl_stats_conn(self, conn, user_id: int, chat_id: int, pnl_pct: float):
        # ── Global stats ──────────────────────────────────────────────
        conn.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
        g = dict(conn.execute(
            "SELECT * FROM user_stats WHERE user_id=?", (user_id,)
        ).fetchone())
        gc = (g["closed_calls"] or 0) + 1
        gt = (g["total_pnl"] or 0.0) + pnl_pct
        conn.execute("""
            UPDATE user_stats SET
                closed_calls=?, wins=?, losses=?,
                total_pnl=?, avg_pnl=?, best_call=?, worst_call=?
            WHERE user_id=?
        """, (
            gc,
            (g["wins"] or 0) + (1 if pnl_pct >= 0 else 0),
            (g["losses"] or 0) + (1 if pnl_pct < 0 else 0),
            gt, gt / gc,
            max(g["best_call"] or 0.0, pnl_pct),
            min(g["worst_call"] or 0.0, pnl_pct),
            user_id
        ))

        # ── Group stats ───────────────────────────────────────────────
        if chat_id:
            conn.execute("""
                INSERT OR IGNORE INTO group_user_stats (chat_id, user_id) VALUES (?, ?)
            """, (chat_id, user_id))
            gp = dict(conn.execute(
                "SELECT * FROM group_user_stats WHERE chat_id=? AND user_id=?",
                (chat_id, user_id)
            ).fetchone())
            gpc = (gp["closed_calls"] or 0) + 1
            gpt = (gp["total_pnl"] or 0.0) + pnl_pct
            conn.execute("""
                UPDATE group_user_stats SET
                    closed_calls=?, wins=?, losses=?,
                    total_pnl=?, avg_pnl=?, best_call=?, worst_call=?
                WHERE chat_id=? AND user_id=?
            """, (
                gpc,
                (gp["wins"] or 0) + (1 if pnl_pct >= 0 else 0),
                (gp["losses"] or 0) + (1 if pnl_pct < 0 else 0),
                gpt, gpt / gpc,
                max(gp["best_call"] or 0.0, pnl_pct),
                min(gp["worst_call"] or 0.0, pnl_pct),
                chat_id, user_id
            ))

    def mark_spike_alerted(self, call_id: int):
        with self._conn() as conn:
            conn.execute("UPDATE calls SET spike_alerted=1 WHERE id=?", (call_id,))

    def increment_duplicates(self, user_id: int, chat_id: int = 0):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO user_stats (user_id, duplicates) VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET duplicates = duplicates + 1
            """, (user_id,))
            if chat_id:
                conn.execute("""
                    INSERT INTO group_user_stats (chat_id, user_id, duplicates) VALUES (?, ?, 1)
                    ON CONFLICT(chat_id, user_id) DO UPDATE SET duplicates = duplicates + 1
                """, (chat_id, user_id))

    def increment_got_copied(self, user_id: int, chat_id: int = 0):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO user_stats (user_id, got_copied) VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET got_copied = got_copied + 1
            """, (user_id,))
            if chat_id:
                conn.execute("""
                    INSERT INTO group_user_stats (chat_id, user_id, got_copied) VALUES (?, ?, 1)
                    ON CONFLICT(chat_id, user_id) DO UPDATE SET got_copied = got_copied + 1
                """, (chat_id, user_id))

    # ─────────────────────────────────────────────────────────────────
    # USER STATS
    # ─────────────────────────────────────────────────────────────────
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT s.*, u.username, u.first_name
                FROM user_stats s JOIN users u ON s.user_id = u.user_id
                WHERE s.user_id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def get_user_group_stats(self, user_id: int, chat_id: int) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT g.*, u.username, u.first_name
                FROM group_user_stats g JOIN users u ON g.user_id = u.user_id
                WHERE g.user_id = ? AND g.chat_id = ?
            """, (user_id, chat_id)).fetchone()
            return dict(row) if row else None

    # ─────────────────────────────────────────────────────────────────
    # LEADERBOARD ENGINE
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _period_clause(period: str, alias: str = "c") -> str:
        if period == "week":
            return f"AND {alias}.closed_at >= datetime('now', '-7 days')"
        elif period == "month":
            return f"AND {alias}.closed_at >= datetime('now', '-30 days')"
        elif period == "today":
            return f"AND date({alias}.closed_at) = date('now')"
        return ""

    @staticmethod
    def _sort_order(sort: str, shame: bool) -> str:
        mapping = {
            "avg_pnl":      ("avg_pnl DESC",        "avg_pnl ASC"),
            "win_rate":     ("win_rate DESC",        "win_rate ASC"),
            "total_calls":  ("closed_calls DESC",    "closed_calls ASC"),
            "best_call":    ("best_call DESC",       "best_call ASC"),
            "worst_call":   ("worst_call DESC",      "worst_call ASC"),
            "total_pnl":    ("total_pnl DESC",       "total_pnl ASC"),
            "consistency":  ("consistency_score DESC", "consistency_score ASC"),
        }
        normal, shamed = mapping.get(sort, mapping["avg_pnl"])
        return shamed if shame else normal

    def get_leaderboard_global(self, sort: str = "avg_pnl",
                               period: str = "all", limit: int = 10) -> List[Dict]:
        return self._leaderboard(None, sort, period, limit, False)

    def get_shame_global(self, sort: str = "avg_pnl",
                         period: str = "all", limit: int = 10) -> List[Dict]:
        return self._leaderboard(None, sort, period, limit, True)

    def get_leaderboard_group(self, chat_id: int, sort: str = "avg_pnl",
                              period: str = "all", limit: int = 10) -> List[Dict]:
        return self._leaderboard(chat_id, sort, period, limit, False)

    def get_shame_group(self, chat_id: int, sort: str = "avg_pnl",
                        period: str = "all", limit: int = 10) -> List[Dict]:
        return self._leaderboard(chat_id, sort, period, limit, True)

    def _leaderboard(self, chat_id: Optional[int], sort: str,
                     period: str, limit: int, shame: bool) -> List[Dict]:
        """
        Unified leaderboard query.
        period == 'all'  → use pre-aggregated stats tables (fast).
        period != 'all'  → compute live from calls (accurate window).
        """
        with self._conn() as conn:
            if period == "all":
                return self._lb_stats_table(conn, chat_id, sort, limit, shame)
            return self._lb_calls_table(conn, chat_id, sort, period, limit, shame)

    def _lb_stats_table(self, conn, chat_id: Optional[int],
                        sort: str, limit: int, shame: bool) -> List[Dict]:
        win_expr = "CAST(wins AS REAL) / NULLIF(wins+losses,0) * 100"
        cs_expr  = f"avg_pnl * CAST(wins AS REAL) / NULLIF(wins+losses,1)"

        if chat_id:
            q = f"""
                SELECT g.*, u.username, u.first_name,
                       ({win_expr}) AS win_rate,
                       ({cs_expr})  AS consistency_score
                FROM group_user_stats g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.chat_id = ? AND g.closed_calls >= 1
                ORDER BY {self._sort_order(sort, shame)}
                LIMIT ?
            """
            rows = conn.execute(q, (chat_id, limit)).fetchall()
        else:
            q = f"""
                SELECT s.*, u.username, u.first_name,
                       ({win_expr}) AS win_rate,
                       ({cs_expr})  AS consistency_score
                FROM user_stats s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.closed_calls >= 1
                ORDER BY {self._sort_order(sort, shame)}
                LIMIT ?
            """
            rows = conn.execute(q, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def _lb_calls_table(self, conn, chat_id: Optional[int], sort: str,
                        period: str, limit: int, shame: bool) -> List[Dict]:
        period_sql  = self._period_clause(period, "c")
        chat_filter = "AND c.chat_id = ?" if chat_id else ""
        params: list = [chat_id] if chat_id else []

        q = f"""
            SELECT
                c.user_id,
                u.username,
                u.first_name,
                COUNT(*)                                                    AS closed_calls,
                SUM(CASE WHEN c.pnl_pct >= 0 THEN 1 ELSE 0 END)            AS wins,
                SUM(CASE WHEN c.pnl_pct <  0 THEN 1 ELSE 0 END)            AS losses,
                SUM(c.pnl_pct)                                              AS total_pnl,
                AVG(c.pnl_pct)                                              AS avg_pnl,
                MAX(c.pnl_pct)                                              AS best_call,
                MIN(c.pnl_pct)                                              AS worst_call,
                CAST(SUM(CASE WHEN c.pnl_pct >= 0 THEN 1 ELSE 0 END) AS REAL)
                    / NULLIF(COUNT(*), 0) * 100                             AS win_rate,
                AVG(c.pnl_pct) *
                    CAST(SUM(CASE WHEN c.pnl_pct >= 0 THEN 1 ELSE 0 END) AS REAL)
                    / NULLIF(COUNT(*), 1)                                   AS consistency_score
            FROM calls c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.status = 'closed'
              {chat_filter}
              {period_sql}
            GROUP BY c.user_id
            HAVING closed_calls >= 1
            ORDER BY {self._sort_order(sort, shame)}
            LIMIT ?
        """
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    # ─────────────────────────────────────────────────────────────────
    # GROUP-LEVEL ANALYTICS
    # ─────────────────────────────────────────────────────────────────
    def get_group_summary(self, chat_id: int) -> Dict:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(DISTINCT user_id)                            AS unique_callers,
                    COUNT(*)                                           AS total_calls,
                    SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END)  AS closed_calls,
                    SUM(CASE WHEN status='open'   THEN 1 ELSE 0 END)  AS open_calls,
                    AVG(CASE WHEN status='closed' THEN pnl_pct END)   AS avg_pnl,
                    MAX(CASE WHEN status='closed' THEN pnl_pct END)   AS best_call,
                    MIN(CASE WHEN status='closed' THEN pnl_pct END)   AS worst_call,
                    SUM(CASE WHEN is_duplicate=1  THEN 1 ELSE 0 END)  AS duplicates
                FROM calls WHERE chat_id = ?
            """, (chat_id,)).fetchone()
            return dict(row) if row else {}

    def get_top_coins_group(self, chat_id: int, limit: int = 5) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT coin,
                       COUNT(*) AS call_count,
                       AVG(CASE WHEN status='closed' THEN pnl_pct END) AS avg_pnl,
                       SUM(CASE WHEN status='closed' AND pnl_pct>=0 THEN 1 ELSE 0 END) AS wins,
                       SUM(CASE WHEN status='closed' AND pnl_pct<0  THEN 1 ELSE 0 END) AS losses
                FROM calls WHERE chat_id = ?
                GROUP BY coin ORDER BY call_count DESC LIMIT ?
            """, (chat_id, limit)).fetchall()
            return [dict(r) for r in rows]

    def get_top_coins_global(self, limit: int = 10) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT coin,
                       COUNT(*) AS call_count,
                       AVG(CASE WHEN status='closed' THEN pnl_pct END) AS avg_pnl,
                       SUM(CASE WHEN status='closed' AND pnl_pct>=0 THEN 1 ELSE 0 END) AS wins,
                       SUM(CASE WHEN status='closed' AND pnl_pct<0  THEN 1 ELSE 0 END) AS losses
                FROM calls
                GROUP BY coin ORDER BY call_count DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_head_to_head(self, user_a: int, user_b: int,
                         chat_id: int = 0) -> Dict:
        with self._conn() as conn:
            chat_filter = "AND chat_id = ?" if chat_id else ""

            def fetch(uid: int) -> Dict:
                params = [uid]
                if chat_id:
                    params.append(chat_id)
                row = conn.execute(f"""
                    SELECT COUNT(*) AS closed_calls,
                           AVG(pnl_pct) AS avg_pnl,
                           MAX(pnl_pct) AS best_call,
                           MIN(pnl_pct) AS worst_call,
                           SUM(CASE WHEN pnl_pct>=0 THEN 1 ELSE 0 END) AS wins
                    FROM calls
                    WHERE user_id=? AND status='closed' {chat_filter}
                """, params).fetchone()
                return dict(row) if row else {}

            return {
                "user_a": {**self.get_user(user_a), **fetch(user_a)},
                "user_b": {**self.get_user(user_b), **fetch(user_b)},
            }

    def get_streak(self, user_id: int, chat_id: int = 0) -> Dict:
        with self._conn() as conn:
            chat_filter = "AND chat_id = ?" if chat_id else ""
            params = [user_id]
            if chat_id:
                params.append(chat_id)
            rows = conn.execute(f"""
                SELECT pnl_pct FROM calls
                WHERE user_id=? AND status='closed' {chat_filter}
                ORDER BY closed_at DESC LIMIT 20
            """, params).fetchall()

        if not rows:
            return {"type": None, "count": 0}
        pnls = [r["pnl_pct"] for r in rows]
        is_win = pnls[0] >= 0
        count = sum(1 for _ in (p for p in pnls if (p >= 0) == is_win)
                    if True)
        # Proper streak count
        streak = 0
        for p in pnls:
            if (p >= 0) == is_win:
                streak += 1
            else:
                break
        return {"type": "win" if is_win else "loss", "count": streak}

    def get_network_stats(self) -> Dict:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users)                      AS total_users,
                    (SELECT COUNT(*) FROM groups WHERE is_active=1)   AS total_groups,
                    COUNT(*)                                          AS total_calls,
                    SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_calls,
                    AVG(CASE WHEN status='closed' THEN pnl_pct END)  AS global_avg_pnl,
                    MAX(CASE WHEN status='closed' THEN pnl_pct END)  AS best_call_ever,
                    MIN(CASE WHEN status='closed' THEN pnl_pct END)  AS worst_call_ever,
                    COUNT(DISTINCT coin)                             AS unique_coins
                FROM calls
            """).fetchone()
            return dict(row) if row else {}
