import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import random
import asyncio
import requests
from transformers import pipeline

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)
pipe = pipeline("text-generation", model="tiny/", device_map="auto")


def get_response(message):
    messages = [
        {"role": "user", "content": message},
    ]
    prompt = pipe.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    outputs = pipe(
        prompt,
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.7,
        top_k=50,
        top_p=0.95,
    )
    return outputs[0]["generated_text"]


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.command()
async def cat(ctx):
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        cat_image_link = data[0]["url"]
        await ctx.send(f"Here's a cat for you: {cat_image_link}")
    else:
        await ctx.send("Failed to fetch cat image. Try again later.")


@bot.command()
async def dog(ctx):
    try:
        response = requests.get("https://api.thedogapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            dog_image_link = data[0]["url"]
            await ctx.send(f"Here's a dog for you: {dog_image_link}")
        else:
            await ctx.send("Failed to fetch dog image. Try again later.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    print("Secret Number:", secret_number)
    await ctx.send("Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                await ctx.send("You guessed it!")
            else:
                await ctx.send("Nope, try again.")
        else:
            await ctx.send("Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        await ctx.send("Time is up! You took too long to guess.")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}!")


@bot.command()
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.send(f"You rolled a {result}.")


@bot.command()
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"The coin landed on: **{result}**")


@bot.command()
async def shalli(ctx):
    result = random.choice(["Yes", "No"])
    await ctx.send(result)


@bot.command()
async def chat(ctx, *, message):
    full_response = get_response(message)
    simplified_response = full_response.split("</s>")[1].strip()
    simplified_response = simplified_response.replace("<|assistant|>\n", "")
    if len(simplified_response) > 2000:
        parts = [
            simplified_response[i : i + 2000]
            for i in range(0, len(simplified_response), 2000)
        ]
        for part in parts:
            await ctx.message.reply(part)
    else:
        await ctx.message.reply(simplified_response)


bot.run(os.getenv("TOKEN"))
