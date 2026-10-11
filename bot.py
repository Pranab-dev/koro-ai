import asyncio
import os
import random
import time
import memory
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

from ai import ask_friend, set_mode, get_mode

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GITHUB = "https://github.com/Pranab-dev/koro-ai"

start_time = time.time()

# INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ======================
# MEMORY HELPERS
# ======================

def is_server_admin(member):
    """Require Discord's administrator permission."""
    return (
        isinstance(member, discord.Member)
        and member.guild_permissions.administrator
    )


def is_private_channel(channel):
    """Treat channels hidden from @everyone as private by default."""
    if isinstance(channel, discord.Thread):
        return channel.is_private()

    guild = getattr(channel, "guild", None)
    if guild is None:
        return True

    default_role = guild.default_role
    permissions = channel.permissions_for(default_role)

    return not permissions.view_channel


def can_read_channel(channel, member):
    """Check that the user and bot can access channel history."""
    user_permissions = channel.permissions_for(member)
    bot_member = channel.guild.me

    if bot_member is None:
        return False

    bot_permissions = channel.permissions_for(bot_member)

    return (
        user_permissions.view_channel
        and bot_permissions.view_channel
        and bot_permissions.read_message_history
    )


def get_searchable_channels(guild, member):
    """
    Return only enabled channels the requester may view and the bot
    can read. Private channels require an explicit admin opt-in.
    """
    candidates = list(guild.text_channels)

    # Include currently cached threads; private threads remain opt-in.
    candidates.extend(
        thread
        for thread in guild.threads
        if thread not in candidates
    )

    allowed = []

    for channel in candidates:
        try:
            if not can_read_channel(channel, member):
                continue

            if not memory.is_channel_enabled(
                guild.id,
                channel.id,
                is_private=is_private_channel(channel),
            ):
                continue

            allowed.append(channel.id)

        except (AttributeError, discord.DiscordException):
            continue

    return allowed


def remember_discord_message(message):
    """Store a Discord message through the memory module."""
    if message.guild is None or message.author.bot:
        return False

    if not message.content or message.content.startswith("!"):
        return False

    if not isinstance(
        message.channel,
        (discord.TextChannel, discord.Thread),
    ):
        return False

    return memory.store_message(
        guild_id=message.guild.id,
        channel_id=message.channel.id,
        message_id=message.id,
        author_id=message.author.id,
        author_name=message.author.display_name,
        content=message.content,
        created_at=message.created_at.timestamp(),
        is_private=is_private_channel(message.channel),
    )

# ======================
# MEMORY EVENTS
# ======================

@bot.listen("on_message")
async def memory_on_message(message):
    try:
        await asyncio.to_thread(
            remember_discord_message,
            message,
        )
    except Exception as exc:
        print("MEMORY STORE ERROR:", exc)


@bot.listen("on_message_edit")
async def memory_on_message_edit(before, after):
    try:
        if after.guild is None:
            return

        if after.author.bot or not after.content:
            await asyncio.to_thread(
                memory.delete_message,
                after.guild.id,
                after.id,
            )
            return

        await asyncio.to_thread(
            remember_discord_message,
            after,
        )
    except Exception as exc:
        print("MEMORY EDIT ERROR:", exc)


@bot.listen("on_message_delete")
async def memory_on_message_delete(message):
    try:
        if message.guild is not None:
            await asyncio.to_thread(
                memory.delete_message,
                message.guild.id,
                message.id,
            )
    except Exception as exc:
        print("MEMORY DELETE ERROR:", exc)

# ======================
# MEMORY COMMANDS
# ======================

memory_group = app_commands.Group(
    name="memory",
    description="Manage Koro's server-specific memory",
)


@memory_group.command(
    name="status",
    description="View this server's memory status",
)
async def memory_status(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Use this command inside a server.",
            ephemeral=True,
        )
        return

    stats = await asyncio.to_thread(
        memory.get_stats,
        interaction.guild.id,
    )

    embed = discord.Embed(
        title="🧠 Koro Memory Status",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Collection",
        value="Enabled" if stats["enabled"] else "Disabled",
        inline=True,
    )
    embed.add_field(
        name="Archived messages",
        value=str(stats["messages"]),
        inline=True,
    )
    embed.add_field(
        name="Channels represented",
        value=str(stats["channels"]),
        inline=True,
    )
    embed.add_field(
        name="Collection notice",
        value=(
            "Acknowledged"
            if stats["notice_acknowledged"]
            else "Not acknowledged"
        ),
        inline=False,
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )


@memory_group.command(
    name="enable",
    description="Enable server memory after displaying the collection notice",
)
async def memory_enable(interaction: discord.Interaction):
    if interaction.guild is None or not is_server_admin(interaction.user):
        await interaction.response.send_message(
            "Administrator permission is required.",
            ephemeral=True,
        )
        return

    notice = (
        "🧠 **Koro server memory notice**\n\n"
        "This server is preparing to enable Koro's memory. Once enabled, "
        "Koro will archive messages in eligible channels to answer "
        "future questions using server context. Messages may be retained "
        "until a server administrator clears them. Private channels are "
        "excluded unless an administrator explicitly enables them. "
        "Koro cannot access channels it lacks permission to read. "
        "Use `/memory disable` to stop collection and `/memory clear` "
        "to delete the archive.\n\n"
        "A server administrator must confirm below to enable collection."
    )

    view = MemoryEnableView(interaction.guild.id)

    await interaction.response.send_message(
        notice,
        view=view,
    )


@memory_group.command(
    name="disable",
    description="Stop collecting new messages in this server",
)
async def memory_disable(interaction: discord.Interaction):
    if interaction.guild is None or not is_server_admin(interaction.user):
        await interaction.response.send_message(
            "Administrator permission is required.",
            ephemeral=True,
        )
        return

    await asyncio.to_thread(
        memory.set_guild_enabled,
        interaction.guild.id,
        False,
        interaction.user.id,
    )

    await interaction.response.send_message(
        "⏸️ Server memory is disabled. New messages will not be collected. "
        "Previously archived messages remain until an administrator clears them.",
        ephemeral=True,
    )


@memory_group.command(
    name="channel-enable",
    description="Enable memory for a specific text channel",
)
@app_commands.describe(channel="Channel to include in memory")
async def memory_channel_enable(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
):
    if interaction.guild is None or not is_server_admin(interaction.user):
        await interaction.response.send_message(
            "Administrator permission is required.",
            ephemeral=True,
        )
        return

    if channel.guild.id != interaction.guild.id:
        await interaction.response.send_message(
            "Choose a channel from this server.",
            ephemeral=True,
        )
        return

    if not channel.permissions_for(interaction.guild.me).view_channel:
        await interaction.response.send_message(
            "Koro cannot view that channel.",
            ephemeral=True,
        )
        return

    await asyncio.to_thread(
        memory.set_channel_enabled,
        interaction.guild.id,
        channel.id,
        True,
        interaction.user.id,
    )

    await interaction.response.send_message(
        f"✅ {channel.mention} is enabled for memory. "
        "If this is a private channel, only members who can access it "
        "will be eligible to search its contents.",
        ephemeral=True,
    )


@memory_group.command(
    name="channel-disable",
    description="Disable memory for a text channel and clear its archive",
)
@app_commands.describe(channel="Channel to exclude from memory")
async def memory_channel_disable(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
):
    if interaction.guild is None or not is_server_admin(interaction.user):
        await interaction.response.send_message(
            "Administrator permission is required.",
            ephemeral=True,
        )
        return

    if channel.guild.id != interaction.guild.id:
        await interaction.response.send_message(
            "Choose a channel from this server.",
            ephemeral=True,
        )
        return

    await asyncio.to_thread(
        memory.set_channel_enabled,
        interaction.guild.id,
        channel.id,
        False,
        interaction.user.id,
    )

    deleted = await asyncio.to_thread(
        memory.clear_channel_memory,
        interaction.guild.id,
        channel.id,
    )

    await interaction.response.send_message(
        f"🔒 {channel.mention} is disabled for memory. "
        f"Removed {deleted} archived messages from that channel.",
        ephemeral=True,
    )


@memory_group.command(
    name="search",
    description="Search this server's accessible memory",
)
@app_commands.describe(query="Keywords to search for")
async def memory_search(
    interaction: discord.Interaction,
    query: str,
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Use this command inside a server.",
            ephemeral=True,
        )
        return

    if not memory.is_guild_enabled(interaction.guild.id):
        await interaction.response.send_message(
            "Server memory is disabled.",
            ephemeral=True,
        )
        return

    allowed_channels = get_searchable_channels(
        interaction.guild,
        interaction.user,
    )

    results = await asyncio.to_thread(
        memory.search_messages,
        interaction.guild.id,
        query,
        allowed_channels,
        8,
    )

    if not results:
        await interaction.response.send_message(
            "No matching messages found in channels you can access.",
            ephemeral=True,
        )
        return

    lines = []

    for row in results:
        channel = interaction.guild.get_channel(
            int(row["channel_id"])
        )
        channel_label = (
            channel.mention if channel is not None else "Unknown channel"
        )
        snippet = row["content"].replace("\n", " ")[:300]

        lines.append(
            f"**{row['author_name']}** in {channel_label}:\n{snippet}"
        )

    await interaction.response.send_message(
        "\n\n".join(lines)[:1900],
        ephemeral=True,
    )


class MemoryEnableView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Confirm and enable",
        style=discord.ButtonStyle.success,
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if (
            interaction.guild is None
            or interaction.guild.id != self.guild_id
            or not is_server_admin(interaction.user)
        ):
            await interaction.response.send_message(
                "Only an administrator of this server can confirm.",
                ephemeral=True,
            )
            return

        await asyncio.to_thread(
            memory.set_guild_enabled,
            self.guild_id,
            True,
            interaction.user.id,
            True,
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=(
                "✅ Server memory is enabled. Eligible public channels "
                "will be collected; private channels remain excluded "
                "until explicitly enabled."
            ),
            view=self,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Memory setup cancelled. Collection remains disabled.",
            view=self,
        )


class MemoryClearView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Permanently clear archive",
        style=discord.ButtonStyle.danger,
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if (
            interaction.guild is None
            or interaction.guild.id != self.guild_id
            or not is_server_admin(interaction.user)
        ):
            await interaction.response.send_message(
                "Only an administrator of this server can clear memory.",
                ephemeral=True,
            )
            return

        deleted = await asyncio.to_thread(
            memory.clear_guild_memory,
            self.guild_id,
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"🗑️ Cleared {deleted} archived messages for this server.",
            view=self,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Archive clearing cancelled.",
            view=self,
        )


@memory_group.command(
    name="clear",
    description="Permanently delete this server's archived messages",
)
async def memory_clear(interaction: discord.Interaction):
    if interaction.guild is None or not is_server_admin(interaction.user):
        await interaction.response.send_message(
            "Administrator permission is required.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "⚠️ **Permanently delete this server's archived messages?** "
        "This cannot be undone. Server settings will remain unchanged.",
        view=MemoryClearView(interaction.guild.id),
        ephemeral=True,
    )


bot.tree.add_command(memory_group)

# EVENTS
@bot.event
async def on_ready():
    try:
        # Set your custom status text here
        custom_status = discord.CustomActivity(name="/help • https://discord.gg/2yJEmys3by")
        await bot.change_presence(activity=custom_status, status=discord.Status.online)
        
        # Sync your slash commands
        synced = await bot.tree.sync()
        print(f"✔️ Synced {len(synced)} slash commands")
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        
    print(f"🤖 Koro online as {bot.user}")


# ======================
# AI COMMANDS# ======================


@bot.command()
async def chat(ctx, *, message=None):

    if not message:
        await ctx.send(
            "Enter something before chatting bruh🥀💔."
        )
        return

    async with ctx.typing():
        try:
            memory_context = None

            # Retrieve server-specific memories only.
            if (
                ctx.guild is not None
                and memory.is_guild_enabled(ctx.guild.id)
            ):
                allowed_channels = get_searchable_channels(
                    ctx.guild,
                    ctx.author,
                )

                results = await asyncio.to_thread(
                    memory.search_messages,
                    ctx.guild.id,
                    message,
                    allowed_channels,
                    8,
                )

                if results:
                    memory_lines = []

                    for row in results:
                        channel = ctx.guild.get_channel(
                            int(row["channel_id"])
                        )

                        channel_name = (
                            f"#{channel.name}"
                            if channel is not None
                            else "unknown-channel"
                        )

                        memory_lines.append(
                            f"[{channel_name}] "
                            f"{row['author_name']}: "
                            f"{row['content'][:500]}"
                        )

                    memory_context = "\n".join(memory_lines)

            reply = await asyncio.to_thread(
                ask_friend,
                message,
                memory_context,
            )

            if len(reply) <= 2000:
                await ctx.send(reply)
            else:
                for i in range(0, len(reply), 2000):
                    await ctx.send(reply[i:i + 2000])

        except Exception as e:
            print("CHAT ERROR:", e)

            await ctx.send(
                "AI BRAINCELSS FRIED. Please try again later."
            )


@bot.tree.command(
    name="mode",
    description="Change Koro's personality"
)
@app_commands.describe(
    mode="normal, brainrot, socrates or random"
)
async def mode(
    interaction: discord.Interaction,
    mode: str
):

    mode = mode.lower()

    if set_mode(mode):

        if mode == "random":

            await interaction.response.send_message(
                "🎲 Koro is now random again."
            )

        else:

            await interaction.response.send_message(
                f"🔄 Koro changed to "
                f"**{mode.upper()} MODE**."
            )

    else:

        await interaction.response.send_message(
            "❌ Invalid mode."
        )


@bot.tree.command(
    name="status",
    description="Show Koro's current mode"
)
async def status(
    interaction: discord.Interaction
):

    current = get_mode()

    if current == "random":

        text = (
            "🎲 Current mode: **RANDOM**\n"
            "10% Normal / 45% Brainrot / 45% Socrates"
        )

    else:

        text = (
            f"🎭 Current mode: "
            f"**{current.upper()} MODE**"
        )

    await interaction.response.send_message(
        text
    )


# ======================
# INFORMATION
# ======================

@bot.tree.command(
    name="help",
    description="Show Koro commands"
)
async def help_command(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🤖 Koro Commands",
        description="Here are Koro's commands:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="AI",
        value="!chat\n/mode\n/status",
        inline=False
    )

    embed.add_field(
        name="Info",
        value="/help\n/about\n/invite",
        inline=False
    )

    embed.add_field(
        name="Utility",
        value="/ping\n/uptime",
        inline=False
    )

    embed.add_field(
        name="User & Server",
        value="/userinfo\n/server\n/membercount",
        inline=False
    )

    embed.add_field(
        name="Fun",
        value="/coinflip\n/dice\n/joke",
        inline=False
    )

    embed.add_field(
        name="Support",
        value="/support\n/feedback",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="about",
    description="About Koro"
)
async def about(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🤖 Koro",
        description="An AI-powered Discord bot.",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="AI Model",
        value="Cohere North Mini Code",
        inline=False
    )

    embed.add_field(
        name="Developer",
        value="@thepixelriftx",
        inline=False
    )

    embed.add_field(
        name="GitHub",
        value=GITHUB,
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="invite",
    description="Invite Koro to your server"
)
async def invite(
    interaction: discord.Interaction
):

    invite_link = (
        "https://discord.com/oauth2/authorize"
        "?client_id=1368858230993719308"
        "&permissions=68608"
        "&integration_type=0"
        "&scope=bot"
    )

    embed = discord.Embed(
        title="🤖 Invite Koro",
        description=(
            "Add Koro to your Discord server:\n\n"
            f"[Click here to invite Koro]({invite_link})"
        ),
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ======================
# UTILITY
# ======================

@bot.tree.command(
    name="ping",
    description="Check latency"
)
async def ping(
    interaction: discord.Interaction
):

    latency = round(
        bot.latency * 1000
    )

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )


@bot.tree.command(
    name="uptime",
    description="Show Koro uptime"
)
async def uptime(
    interaction: discord.Interaction
):

    seconds = int(
        time.time() - start_time
    )

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    await interaction.response.send_message(
        f"⏱ Online for **{hours}h {minutes}m**"
    )


# ======================
# USER / SERVER
# ======================

@bot.tree.command(
    name="userinfo",
    description="Show user information"
)
@app_commands.describe(
    user="User to check"
)
async def userinfo(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    user = user or interaction.user

    embed = discord.Embed(
        title=f"👤 {user.name}",
        color=discord.Color.green()
    )

    embed.set_thumbnail(
        url=user.display_avatar.url
    )

    embed.add_field(
        name="ID",
        value=user.id
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="server",
    description="Show server information"
)
async def server(
    interaction: discord.Interaction
):

    guild = interaction.guild

    embed = discord.Embed(
        title=f"🏠 {guild.name}",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="Members",
        value=guild.member_count
    )

    embed.add_field(
        name="Owner",
        value=guild.owner
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="membercount",
    description="Show member count"
)
async def membercount(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"👥 Members: **{interaction.guild.member_count}**"
    )


# ======================
# FUN
# ======================

@bot.tree.command(
    name="coinflip",
    description="Flip a coin"
)
async def coinflip(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        random.choice(
            [
                "🪙 Heads!",
                "🪙 Tails!"
            ]
        )
    )


@bot.tree.command(
    name="dice",
    description="Roll a dice"
)
async def dice(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"🎲 You rolled **{random.randint(1, 6)}**"
    )


@bot.tree.command(
    name="joke",
    description="Tell a joke"
)
async def joke(
    interaction: discord.Interaction
):

    jokes = [
        "404 joke not found."
    ]

    await interaction.response.send_message(
        random.choice(jokes)
    )


# ======================
# SUPPORT
# ======================

@bot.tree.command(
    name="support",
    description="Get Koro support"
)
async def support(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"🛠 Koro Support\n\n"
        f"GitHub:\n{GITHUB}"
    )


@bot.tree.command(
    name="feedback",
    description="Send feedback"
)
async def feedback(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"💡 Submit feedback here:\n"
        f"{GITHUB}/issues"
    )


# ======================
# START KORO
# ======================

bot.run(TOKEN)