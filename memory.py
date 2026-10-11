import os
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


# =========================
# CONFIGURATION
# =========================

DEFAULT_DB_PATH = Path("data") / "koro_memory.sqlite3"
DB_PATH = Path(
    os.getenv("KORO_MEMORY_DB_PATH", str(DEFAULT_DB_PATH))
)

MAX_MESSAGE_LENGTH = 4000
DEFAULT_SEARCH_LIMIT = 8
MAX_SEARCH_LIMIT = 20


# =========================
# DATABASE
# =========================

@contextmanager
def _connect():
    """Open a database connection with safe defaults."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10
    )
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Create Koro's persistent memory tables and search index."""
    with _connect() as db:
        db.execute("PRAGMA journal_mode = WAL")

        db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0,
                notice_acknowledged INTEGER NOT NULL DEFAULT 0,
                updated_by TEXT,
                updated_at REAL NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS channel_settings (
                guild_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                updated_by TEXT,
                updated_at REAL NOT NULL,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                guild_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                edited_at REAL,
                PRIMARY KEY (guild_id, message_id)
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_guild_channel
            ON messages (guild_id, channel_id, created_at)
        """)

        # FTS5 provides efficient full-text search.
        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS message_search
            USING fts5(
                guild_id UNINDEXED,
                channel_id UNINDEXED,
                message_id UNINDEXED,
                author_name,
                content,
                tokenize = 'unicode61'
            )
        """)


# =========================
# SERVER SETTINGS
# =========================

def get_guild_settings(guild_id):
    """Return settings for one server, creating defaults if needed."""
    guild_id = str(guild_id)

    with _connect() as db:
        db.execute("""
            INSERT OR IGNORE INTO guild_settings (
                guild_id, enabled, notice_acknowledged, updated_at
            )
            VALUES (?, 0, 0, ?)
        """, (guild_id, time.time()))

        row = db.execute("""
            SELECT enabled, notice_acknowledged, updated_by, updated_at
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

        return dict(row)


def is_guild_enabled(guild_id):
    settings = get_guild_settings(guild_id)
    return bool(settings["enabled"])


def set_guild_enabled(
    guild_id,
    enabled,
    actor_id,
    notice_acknowledged=False
):
    """
    Enable or disable collection for one server.

    Enabling requires an explicit acknowledgement of the collection notice.
    Call this only after the bot has verified the actor is a server admin.
    """
    guild_id = str(guild_id)
    actor_id = str(actor_id)
    now = time.time()

    with _connect() as db:
        db.execute("""
            INSERT OR IGNORE INTO guild_settings (
                guild_id, enabled, notice_acknowledged, updated_at
            )
            VALUES (?, 0, 0, ?)
        """, (guild_id, now))

        if enabled:
            if not notice_acknowledged:
                raise ValueError(
                    "The server memory notice must be acknowledged "
                    "before enabling collection."
                )

            db.execute("""
                UPDATE guild_settings
                SET enabled = 1,
                    notice_acknowledged = 1,
                    updated_by = ?,
                    updated_at = ?
                WHERE guild_id = ?
            """, (actor_id, now, guild_id))
        else:
            db.execute("""
                UPDATE guild_settings
                SET enabled = 0,
                    updated_by = ?,
                    updated_at = ?
                WHERE guild_id = ?
            """, (actor_id, now, guild_id))


# =========================
# CHANNEL SETTINGS
# =========================

def set_channel_enabled(
    guild_id,
    channel_id,
    enabled,
    actor_id
):
    """
    Explicitly enable or disable a channel.

    An explicit enable also permits an otherwise-private channel, provided
    the bot and the requesting user have the necessary Discord permissions.
    Those Discord permission checks must happen in bot.py.
    """
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    actor_id = str(actor_id)

    with _connect() as db:
        db.execute("""
            INSERT INTO channel_settings (
                guild_id, channel_id, enabled, updated_by, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, channel_id)
            DO UPDATE SET
                enabled = excluded.enabled,
                updated_by = excluded.updated_by,
                updated_at = excluded.updated_at
        """, (
            guild_id,
            channel_id,
            int(bool(enabled)),
            actor_id,
            time.time()
        ))


def is_channel_enabled(guild_id, channel_id, is_private=False):
    """
    Determine whether a channel is eligible for collection.

    Default behavior:
    - Server memory must be enabled.
    - Public channels are included unless explicitly disabled.
    - Private channels are excluded unless explicitly enabled.
    """
    guild_id = str(guild_id)
    channel_id = str(channel_id)

    with _connect() as db:
        server = db.execute("""
            SELECT enabled
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

        if not server or not server["enabled"]:
            return False

        channel = db.execute("""
            SELECT enabled
            FROM channel_settings
            WHERE guild_id = ? AND channel_id = ?
        """, (guild_id, channel_id)).fetchone()

        if channel is not None:
            return bool(channel["enabled"])

        return not is_private


# =========================
# MESSAGE STORAGE
# =========================

def store_message(
    guild_id,
    channel_id,
    message_id,
    author_id,
    author_name,
    content,
    created_at=None,
    is_private=False,
):
    """Store a message only when its server and channel permit collection."""
    content = (content or "").strip()

    if not content:
        return False

    content = content[:MAX_MESSAGE_LENGTH]

    guild_id = str(guild_id)
    channel_id = str(channel_id)
    message_id = str(message_id)
    author_id = str(author_id)
    author_name = str(author_name)[:200]

    # Enforce both server and channel settings before storing.
    if not is_channel_enabled(
        guild_id,
        channel_id,
        is_private=is_private,
    ):
        return False

    created_at = (
        float(created_at)
        if created_at is not None
        else time.time()
    )

    with _connect() as db:
        # Recheck server status while writing.
        settings = db.execute("""
            SELECT enabled
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

        if not settings or not settings["enabled"]:
            return False

        db.execute("""
            DELETE FROM message_search
            WHERE guild_id = ? AND message_id = ?
        """, (guild_id, message_id))

        db.execute("""
            INSERT INTO messages (
                guild_id, channel_id, message_id,
                author_id, author_name, content, created_at, edited_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(guild_id, message_id)
            DO UPDATE SET
                channel_id = excluded.channel_id,
                author_id = excluded.author_id,
                author_name = excluded.author_name,
                content = excluded.content,
                edited_at = ?
        """, (
            guild_id,
            channel_id,
            message_id,
            author_id,
            author_name,
            content,
            created_at,
            time.time(),
        ))

        db.execute("""
            INSERT INTO message_search (
                guild_id, channel_id, message_id, author_name, content
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            guild_id,
            channel_id,
            message_id,
            author_name,
            content,
        ))

    return True

def delete_message(guild_id, message_id):
    """Delete one archived message and its search entry."""
    guild_id = str(guild_id)
    message_id = str(message_id)

    with _connect() as db:
        db.execute("""
            DELETE FROM message_search
            WHERE guild_id = ? AND message_id = ?
        """, (guild_id, message_id))

        cursor = db.execute("""
            DELETE FROM messages
            WHERE guild_id = ? AND message_id = ?
        """, (guild_id, message_id))

        return cursor.rowcount > 0


def clear_guild_memory(guild_id):
    """Delete a server's archived messages without changing its settings."""
    guild_id = str(guild_id)

    with _connect() as db:
        db.execute("""
            DELETE FROM message_search WHERE guild_id = ?
        """, (guild_id,))

        cursor = db.execute("""
            DELETE FROM messages WHERE guild_id = ?
        """, (guild_id,))

        return cursor.rowcount


def clear_channel_memory(guild_id, channel_id):
    """Delete all archived messages belonging to one server channel."""
    guild_id = str(guild_id)
    channel_id = str(channel_id)

    with _connect() as db:
        db.execute("""
            DELETE FROM message_search
            WHERE guild_id = ? AND channel_id = ?
        """, (guild_id, channel_id))

        cursor = db.execute("""
            DELETE FROM messages
            WHERE guild_id = ? AND channel_id = ?
        """, (guild_id, channel_id))

        return cursor.rowcount


# =========================
# SEARCH
# =========================

def search_messages(
    guild_id,
    query,
    allowed_channel_ids,
    limit=DEFAULT_SEARCH_LIMIT
):
    """
    Search messages in one server and an explicitly allowed channel set.

    allowed_channel_ids must be calculated by bot.py using the requesting
    user's current Discord channel permissions and enabled memory settings.
    An omitted or empty allowlist returns no results.
    """
    guild_id = str(guild_id)
    query = (query or "").strip()

    if not query or not allowed_channel_ids:
        return []

    channel_ids = list({
        str(channel_id)
        for channel_id in allowed_channel_ids
    })

    if not channel_ids:
        return []

    limit = max(1, min(int(limit), MAX_SEARCH_LIMIT))

    # Construct a safe FTS expression from individual search terms.
    terms = re.findall(r"\w+", query, flags=re.UNICODE)

    if not terms:
        return []

    # OR permits partial matches when a query contains several keywords.
    expression = " OR ".join(
        '"' + term.replace('"', '""') + '"*'
        for term in terms[:12]
    )

    placeholders = ",".join("?" for _ in channel_ids)

    sql = f"""
        SELECT
            m.guild_id,
            m.channel_id,
            m.message_id,
            m.author_id,
            m.author_name,
            m.content,
            m.created_at,
            m.edited_at
        FROM message_search
        JOIN messages AS m
          ON m.guild_id = message_search.guild_id
         AND m.message_id = message_search.message_id
        WHERE message_search MATCH ?
          AND message_search.guild_id = ?
          AND message_search.channel_id IN ({placeholders})
          AND m.channel_id = message_search.channel_id
        ORDER BY rank
        LIMIT ?
    """

    with _connect() as db:
        rows = db.execute(
            sql,
            [expression, guild_id, *channel_ids, limit]
        ).fetchall()

    return [dict(row) for row in rows]


# =========================
# STATISTICS
# =========================

def get_stats(guild_id):
    """Return archive statistics for a single server."""
    guild_id = str(guild_id)

    with _connect() as db:
        message_count = db.execute("""
            SELECT COUNT(*) AS count
            FROM messages
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()["count"]

        channel_count = db.execute("""
            SELECT COUNT(DISTINCT channel_id) AS count
            FROM messages
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()["count"]

    settings = get_guild_settings(guild_id)

    return {
        "enabled": bool(settings["enabled"]),
        "notice_acknowledged": bool(
            settings["notice_acknowledged"]
        ),
        "messages": message_count,
        "channels": channel_count,
    }


# =========================
# STARTUP
# =========================

initialize_database()
