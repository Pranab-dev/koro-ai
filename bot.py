import asyncio
import os
import random
import time

import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

from ai import ask_friend, set_mode, get_mode

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GITHUB = "https://github.com/Pranab-dev/koro-ai"

start_time = time.time()

# ======================
# SERVER TAG SETTINGS
# ======================

V0ID_TAG = "V0ID"
GUILD_SUPPORTER_ROLE_ID = 1358039885843402832

# ======================
# INTENTS
# ======================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# ======================
# SERVER TAG CHECKER
# ======================

@tasks.loop(seconds=60)
async def check_server_tags():

    for guild in bot.guilds:

        role = guild.get_role(
            GUILD_SUPPORTER_ROLE_ID
        )

        if role is None:
            print(
                f"⚠️ Guild Supporter role not found in {guild.name}"
            )
            continue

        me = guild.me

        if me is None:
            continue

        if not me.guild_permissions.manage_roles:
            print(
                f"❌ Koro needs Manage Roles in {guild.name}"
            )
            continue

        if role >= me.top_role:
            print(
                f"❌ Koro's role must be above "
                f"Guild Supporter in {guild.name}"
            )
            continue

        for member in guild.members:

            # Ignore bots
            if member.bot:
                continue

            primary = member.primary_guild

            has_v0id = (
                primary is not None
                and primary.identity_enabled is True
                and primary.identity_guild_id == guild.id
                and primary.tag == V0ID_TAG
            )

            has_supporter = role in member.roles

            try:

                # V0ID detected → give Guild Supporter
                if has_v0id and not has_supporter:

                    await member.add_roles(
                        role,
                        reason="V0ID Server Tag detected"
                    )

                    print(
                        f"🏷️ Added Guild Supporter to "
                        f"{member} in {guild.name}"
                    )

                # V0ID removed → remove Guild Supporter
                elif not has_v0id and has_supporter:

                    await member.remove_roles(
                        role,
                        reason="V0ID Server Tag no longer detected"
                    )

                    print(
                        f"🏷️ Removed Guild Supporter from "
                        f"{member} in {guild.name}"
                    )

            except discord.Forbidden:
                print(
                    f"❌ Permission error modifying "
                    f"{member} in {guild.name}"
                )

            except discord.HTTPException as e:
                print(
                    f"❌ Discord API error modifying "
                    f"{member}: {e}"
                )


@check_server_tags.before_loop
async def before_check_server_tags():

    await bot.wait_until_ready()


# ======================
# EVENTS
# ======================

@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()

        print(
            f"✅ Synced {len(synced)} slash commands"
        )

    except Exception as e:

        print(
            f"❌ Sync error: {e}"
        )

    if not check_server_tags.is_running():

        check_server_tags.start()

        print(
            "🏷️ Server Tag checker started"
        )

    print(
        f"🤖 Koro online as {bot.user}"
    )


# ======================
# AI COMMANDS
# ======================

@bot.command()
async def chat(ctx, *, message=None):

    if not message:

        await ctx.send(
            "Enter something before chatting bruh🥀💔."
        )

        return

    async with ctx.typing():

        try:

            reply = await asyncio.to_thread(
                ask_friend,
                message
            )

            if len(reply) <= 2000:

                await ctx.send(reply)

            else:

                for i in range(
                    0,
                    len(reply),
                    2000
                ):

                    await ctx.send(
                        reply[i:i + 2000]
                    )

        except Exception as e:

            print(
                "CHAT ERROR:",
                e
            )

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
            f"**{current.upper()}**"
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
        value=(
            "!chat <message>\n"
            "/mode\n"
            "/status"
        ),
        inline=False
    )

    embed.add_field(
        name="Info",
        value=(
            "/help\n"
            "/about\n"
            "/invite"
        ),
        inline=False
    )

    embed.add_field(
        name="Utility",
        value=(
            "/ping\n"
            "/uptime"
        ),
        inline=False
    )

    embed.add_field(
        name="User & Server",
        value=(
            "/userinfo\n"
            "/server\n"
            "/membercount"
        ),
        inline=False
    )

    embed.add_field(
        name="Fun",
        value=(
            "/coinflip\n"
            "/dice\n"
            "/joke"
        ),
        inline=False
    )

    embed.add_field(
        name="Support",
        value=(
            "/support\n"
            "/feedback"
        ),
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
        value="NVIDIA Nemotron Nano 12B",
        inline=False
    )

    embed.add_field(
        name="Developer",
        value="Pranab",
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

    minutes = (
        seconds % 3600
    ) // 60

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
        f"👥 Members: "
        f"**{interaction.guild.member_count}**"
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
        f"🎲 You rolled "
        f"**{random.randint(1, 6)}**"
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