import discord,os,requests
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = discord.Bot()

@bot.command(description="Sends the bot's latency.") 
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is {bot.latency}")
    
@bot.command(description="Sends a cat image.")
async def cat(ctx):
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        cat_image_link = data[0]["url"]
        await ctx.send(f"Here's a cat for you: {cat_image_link}")
    else:
        await ctx.send("Failed to fetch cat image. Try again later.")

bot.run(TOKEN)