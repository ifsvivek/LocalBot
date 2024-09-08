# Mini chatbot using Mistral Nemo


import discord, os, requests, asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("JEFF")


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def fetch_response(prompt):
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {"model": "mistral-nemo:latest", "prompt": prompt, "stream": False}

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: requests.post(url, headers=headers, json=data)
    )
    return response.json()["response"]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(
            ctx, message=message.content.replace(f"<@{bot.user.id}>", "").strip()
        )


@bot.command(description="Chat with the bot.")
async def chat(ctx, *, message):
    async with ctx.typing():
        try:
            response = await fetch_response(message)
            if len(response) > 2000:
                is_first_chunk = True
                while response:
                    split_at = (response[:2000].rfind("\n") + 1) or 2000
                    chunk, response = (
                        response[:split_at].strip(),
                        response[split_at:].strip(),
                    )
                    if is_first_chunk:
                        await ctx.reply(chunk)
                        is_first_chunk = False
                    else:
                        await ctx.send(chunk)
            else:
                await ctx.reply(response)
        except Exception as e:
            print(f"\n\nError: {e}\n\n")
            await ctx.reply("Sorry, I am unable to respond at the moment.")


bot.run(TOKEN)
