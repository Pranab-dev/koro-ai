import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

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
    print(f"Koro AI is online as {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.command()
async def chat(ctx, *, message=None):

    if not message:
        await ctx.send(
            "K-KITTEN 😭 YOU FORGOT TO TELL ME WHAT TO CHAT ABOUT."
        )
        return

    async with ctx.typing():

        try:
            reply = ask_friend(message)

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


@bot.command()
async def koro(ctx, mode=None):

    if mode is None:
        await ctx.send(
            "🗿 Usage: `!koro normal`, `!koro brainrot`, "
            "`!koro socrates`, or `!koro random`"
        )
        return

    mode = mode.lower()

    if set_mode(mode):
        if mode == "random":
            await ctx.send(
                "🎲 Koro's personality is random again."
            )
        else:
            await ctx.send(
                f"🔄 Koro is now in **{mode.upper()} MODE**."
            )
    else:
        await ctx.send(
            "❌ Unknown mode. Try `normal`, `brainrot`, "
            "`socrates`, or `random`."
        )


@bot.command()
async def status(ctx):
    mode = get_mode()

    if mode == "random":
        await ctx.send(
            "🎲 Current mode: **RANDOM** "
            "(10% Normal / 45% Brainrot / 45% Socrates)"
        )
    else:
        await ctx.send(
            f"🎭 Current mode: **{mode.upper()}**"
        )


bot.run(TOKEN)