import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import random
import asyncio
import requests

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(activity=discord.Game(name="Running on phone"))


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(
            ctx, message=message.content.replace(f"<@{bot.user.id}>", "").strip()
        )
    else:
        await bot.process_commands(message)


@bot.command(description="Send a picture of a cat.")
async def cat(ctx):
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        cat_image_link = data[0]["url"]
        await ctx.message.reply(cat_image_link)
    else:
        await ctx.message.reply("Failed to fetch cat image. Try again later.")


@bot.command(description="Send a picture of a dog.")
async def dog(ctx):
    try:
        response = requests.get("https://api.thedogapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            dog_image_link = data[0]["url"]
            await ctx.message.reply(dog_image_link)
        else:
            await ctx.message.reply("Failed to fetch dog image. Try again later.")
    except Exception as e:
        await ctx.message.reply(f"An error occurred: {e}")


@bot.command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    print("Secret Number:", secret_number)
    await ctx.message.reply("Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                await ctx.message.reply("You guessed it!")
            else:
                await ctx.message.reply("Nope, try again.")
        else:
            await ctx.message.reply("Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        await ctx.message.reply("Time is up! You took too long to guess.")


@bot.command(description="Tell the user hello.")
async def hello(ctx):
    await ctx.message.reply(f"Hello, {ctx.author.name}!")


@bot.command(description="Roll a dice with the specified number of sides.")
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.message.reply(f"You rolled a {result}.")


@bot.command(description="Flip a coin.")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.message.reply(f"The coin landed on: **{result}**")


@bot.command(description="Ask the bot a yes/no question.")
async def shalli(ctx):
    result = random.choice(["Yes", "No"])
    await ctx.message.reply(result)


@bot.command()
async def chat(ctx, *, message):
    await ctx.message.reply(
        "I am currently running on a phone, so I am unable to chat."
    )


bot.run(TOKEN)
