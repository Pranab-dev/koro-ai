
import tempfile
from pathlib import Path

import memory

# Use a temporary database so the test cannot touch real memory.
with tempfile.TemporaryDirectory() as temp_dir:
    memory.DB_PATH = Path(temp_dir) / "test.sqlite3"
    memory.initialize_database()

    # Enable two independent servers.
    memory.set_guild_enabled(
        100, True, actor_id=1, notice_acknowledged=True
    )
    memory.set_guild_enabled(
        200, True, actor_id=2, notice_acknowledged=True
    )

    memory.store_message(
        100, 101, 1001, 501, "Alice",
        "We should play Minecraft this weekend."
    )
    memory.store_message(
        200, 201, 2001, 601, "Bob",
        "We should play Roblox this weekend."
    )

    results_a = memory.search_messages(
        100, "Minecraft", allowed_channel_ids=[101]
    )
    results_b = memory.search_messages(
        200, "Minecraft", allowed_channel_ids=[201]
    )

    assert len(results_a) == 1
    assert results_a[0]["guild_id"] == "100"
    assert results_b == []

    memory.delete_message(100, 1001)

    assert memory.search_messages(
        100, "Minecraft", allowed_channel_ids=[101]
    ) == []

    print("PASS: server isolation and deletion work.")
