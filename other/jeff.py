import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("JEFF")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=";", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(ctx)


async def chat(ctx):
    async with ctx.typing():
        await ctx.reply("MY NAME IS JEFF")


@bot.command()
async def jeff(ctx):
    await ctx.send("MY NAME IS JEFF")


bot.run(TOKEN)
