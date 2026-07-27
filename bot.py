import asyncio
import os

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from ai import ask_friend, set_mode, get_mode

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

    print(f"Koro AI is online as {bot.user}")


# ------------------------
# PING
# ------------------------

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")


@bot.tree.command(name="ping", description="Check if Koro is online.")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")


# ------------------------
# CHAT
# ------------------------

@bot.command()
async def chat(ctx, *, message=None):

    if not message:
        await ctx.send(
            "K-KITTEN 😭 YOU FORGOT TO TELL ME WHAT TO CHAT ABOUT."
        )
        return

    async with ctx.typing():
        try:
            reply = await asyncio.to_thread(ask_friend, message)

            if len(reply) <= 2000:
                await ctx.send(reply)
            else:
                for i in range(0, len(reply), 2000):
                    await ctx.send(reply[i:i + 2000])

        except Exception as e:
            print("ERROR:", e)
            await ctx.send(
                "💀 K-KITTEN MY BRAIN EXPLODED. TRY AGAIN."
            )


@bot.tree.command(name="chat", description="Chat with Koro AI.")
@app_commands.describe(message="Your message to Koro")
async def slash_chat(interaction: discord.Interaction, message: str):

    await interaction.response.defer(thinking=True)

    try:
        reply = await asyncio.to_thread(ask_friend, message)

        if len(reply) <= 2000:
            await interaction.followup.send(reply)
        else:
            for i in range(0, len(reply), 2000):
                await interaction.followup.send(reply[i:i + 2000])

    except Exception as e:
        print("ERROR:", e)
        await interaction.followup.send(
            "💀 K-KITTEN MY BRAIN EXPLODED. TRY AGAIN."
        )


# ------------------------
# KORO MODE
# ------------------------

@bot.command()
async def koro(ctx, mode=None):

    if mode is None:
        await ctx.send(
            "🗿 Usage: `!koro normal`, `!koro brainrot`, `!koro socrates`, or `!koro random`"
        )
        return

    mode = mode.lower()

    if set_mode(mode):
        if mode == "random":
            await ctx.send("🎲 Koro's personality is random again.")
        else:
            await ctx.send(f"🔄 Koro is now in **{mode.upper()} MODE**.")
    else:
        await ctx.send(
            "❌ Unknown mode. Try `normal`, `brainrot`, `socrates`, or `random`."
        )


@bot.tree.command(name="koro", description="Change Koro's personality.")
@app_commands.describe(
    mode="normal, brainrot, socrates or random"
)
async def slash_koro(
    interaction: discord.Interaction,
    mode: str
):

    mode = mode.lower()

    if set_mode(mode):
        if mode == "random":
            await interaction.response.send_message(
                "🎲 Koro's personality is random again."
            )
        else:
            await interaction.response.send_message(
                f"🔄 Koro is now in **{mode.upper()} MODE**."
            )
    else:
        await interaction.response.send_message(
            "❌ Unknown mode."
        )


# ------------------------
# STATUS
# ------------------------

@bot.command()
async def status(ctx):

    mode = get_mode()

    if mode == "random":
        await ctx.send(
            "🎲 Current mode: **RANDOM** (10% Normal / 45% Brainrot / 45% Socrates)"
        )
    else:
        await ctx.send(
            f"🎭 Current mode: **{mode.upper()}**"
        )


@bot.tree.command(name="status", description="Show Koro's current mode.")
async def slash_status(interaction: discord.Interaction):

    mode = get_mode()

    if mode == "random":
        await interaction.response.send_message(
            "🎲 Current mode: **RANDOM** (10% Normal / 45% Brainrot / 45% Socrates)"
        )
    else:
        await interaction.response.send_message(
            f"🎭 Current mode: **{mode.upper()}**"
        )


bot.run(TOKEN)