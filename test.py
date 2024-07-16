import discord, json, random, asyncio, os, base64, argparse, time, lyricsgenius
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed
import aiohttp
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import yt_dlp as youtube_dl # Be careful with this sync
from typing import Dict, List, Union, Optional # Added Optional import

load_dotenv()
TOKEN = os.getenv("TOKEN")
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
API_KEY = os.getenv("API_KEY")
SERVER_URL = os.getenv("SERVER_URL")
MODEL_NAME = os.getenv("MODEL")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

music_dir = "music"
os.makedirs(music_dir, exist_ok=True)
genius = lyricsgenius.Genius(GENIUS_TOKEN)
current_song = None
playlist_queue = []
server_state = {}
conversation_history = {}
system_prompt = """
System: This is a system message.
Your name is LocalBot.
You are designed to chat with users and generate images based on prompts.
You can also play songs from YouTube and fetch lyrics for the songs.
If anyone asks why you are named LocalBot, just say that you are a bot that runs locally.
Use emojis but don't overdo it.
Remember to have fun!

COMMANDS:
/cat or $cat: Sends a random cat image.
/dog or $dog: Sends a random dog image.
/gtn or $gtn: Starts a number guessing game.
/hello or $hello: Greets the user.
/dice [sides] or $dice [sides]: Rolls a dice with the specified number of sides (default is 6 if none specified).
/flip or $flip: Flips a coin.
/ask or $ask: Provides a yes/no response randomly.
/chat [message] or $chat [message]: Engages in a chat with the bot using the text-generation model.
$imagine [prompt]: Generates an image based on the provided prompt (--magic for magic prompt, --model to specify the model to use for image generation; range: [0, 1, 2, 3, 4, 5]).
/purge [amount] or $purge [amount]: Deletes the specified number of messages in the channel (requires Manage Messages permission).
$clear [amount]: Clears the specified number of messages in the DM.
/join: Joins the voice channel of the user.
/leave: Leaves the voice channel.
/play [song]: Plays the specified song in the voice channel.
/stop: Stops the currently playing song.
/lyrics [song]: Fetches the lyrics of the specified song.

END OF SYSTEM MESSAGE
"""

ytdl_format_options = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": os.path.join(music_dir, "%(title)s.%(ext)s"),
    "restrictfilenames": True,
    "noplaylist": False,
}

ffmpeg_options = {
    "options": "-vn",
}

async def get_server_state(guild_id):
    if guild_id not in server_state:
        server_state[guild_id] = {"current_song": None, "playlist_queue": []}
    return server_state[guild_id]

async def generate_text(server_id: str, channel_id: str, user_id: str, prompt: str, user_name: str) -> Union[str, None]:
    """
    Generate a response text based on the given prompt and conversation history.

    Args:
        server_id (str): The ID of the server.
        channel_id (str): The ID of the channel.
        user_id (str): The ID of the user.
        prompt (str): The user's prompt.
        user_name (str): The name of the user.

    Returns:
        str: The response from the bot.
        None: In case of an error.
    """
    global conversation_history

    # Initialize the conversation history if it doesn't exist
    if server_id not in conversation_history:
        conversation_history[server_id] = {}
    if channel_id not in conversation_history[server_id]:
        conversation_history[server_id][channel_id] = {}
    if user_id not in conversation_history[server_id][channel_id]:
        conversation_history[server_id][channel_id][user_id] = []

    # Append the user's prompt to the conversation history
    conversation_history[server_id][channel_id][user_id].append(f"{user_name}: {prompt}")

    # Optionally append the system prompt to the conversation history
    if system_prompt:
        conversation_history[server_id][channel_id][user_id].append(f"System: {system_prompt}")

    # Join the conversation history into a single context string
    context = "\n".join(conversation_history[server_id][channel_id][user_id])

    # Define the URL and headers for the API request
    url = f"{SERVER_URL}/ollama/api/generate"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # Define the data payload for the API request
    data = {
        "model": MODEL_NAME,
        "prompt": f"<context>{context}</context>\n\nBot:",
        "stream": False,
    }

    # Make the asynchronous API request
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            # Check if the request was successful
            if response.status == 200:
                result = await response.json()
                # Append the bot's response to the conversation history
                conversation_history[server_id][channel_id][user_id].append(f"Bot: {result['response']}")
                return result["response"]
            else:
                return f"Error: Request failed with status code {response.status}"

async def generate_image(prompt, model_id=0, use_refiner=False, magic_prompt=False, calc_metrics=False):
    output_dir = "img"
    os.makedirs(output_dir, exist_ok=True)

    url = "https://diffusion.ayushmanmuduli.com/gen"
    params = {
        "prompt": prompt,
        "model_id": model_id,
        "use_refiner": use_refiner,
        "magic_prompt": magic_prompt,
        "calc_metrics": calc_metrics,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                base64_image_string = data["image"]
                image_data = base64.b64decode(base64_image_string)
                image = Image.open(BytesIO(image_data))
                timestamp = int(time.time())
                image_path = os.path.join(output_dir, f"img_{timestamp}.png")
                image.save(image_path)

                return image_path
            else:
                return None

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(activity=discord.Game(name="Running on Server"))

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(
            ctx, message=message.content.replace(f"<@{bot.user.id}>", "").strip()
        )
    else:
        await bot.process_commands(message)

@bot.slash_command(description="Send a picture of a cat.")
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            if response.status == 200:
                data = await response.json()
                cat_image_link = data[0]["url"]
                await ctx.respond(cat_image_link)
            else:
                await ctx.respond("Failed to fetch cat image. Try again later.", ephemeral=True)

@bot.slash_command(description="Send a picture of a dog.")
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thedogapi.com/v1/images/search") as response:
            if response.status == 200:
                data = await response.json()
                dog_image_link = data[0]["url"]
                await ctx.respond(dog_image_link)
            else:
                await ctx.respond("Failed to fetch dog image. Try again later.", ephemeral=True)

@bot.slash_command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    print("Secret Number:", secret_number)
    await ctx.respond("Guess a number between 1 and 10!")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    guess = await bot.wait_for("message", check=check)
    guess_number = int(guess.content)
    if guess_number == secret_number:
        await ctx.respond("Congratulations! You guessed the correct number!")
    else:
        await ctx.respond(
            f"Sorry, the correct number was {secret_number}. Better luck next time!"
        )

@bot.slash_command(description="Greet the bot.")
async def hello(ctx):
    await ctx.respond(f"Hello {ctx.author.mention}!")

@bot.slash_command(description="Roll a dice with a specified number of sides (default is 6).")
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.respond(f"🎲 You rolled a {result} on a {sides}-sided dice.")

@bot.slash_command(description="Flip a coin.")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.respond(f"🪙 The coin landed on {result}.")

@bot.slash_command(description="Ask the bot a yes/no question.")
async def ask(ctx):
    response = random.choice(["Yes", "No", "Maybe", "Ask again later"])
    await ctx.respond(f"🔮 {response}")

@bot.slash_command(description="Chat with the bot using a text-generation model.")
async def chat(ctx, *, message: str):
    server_id = str(ctx.guild.id)
    channel_id = str(ctx.channel.id)
    user_id = str(ctx.author.id)
    user_name = str(ctx.author.display_name)

    response = await generate_text(server_id, channel_id, user_id, message, user_name)

    if response:
        await ctx.respond(response)
    else:
        await ctx.respond("Sorry, something went wrong while generating a response.")

@bot.command(description="Generate an image based on a prompt.")
async def imagine(ctx, *, args):
    start_time = time.time()

    args_list = shlex.split(args)
    prompt_parts = []
    while args_list and not args_list[0].startswith("--"):
        prompt_parts.append(args_list.pop(0))
    prompt = " ".join(prompt_parts)
    parser = argparse.ArgumentParser(
        description="Generate an image based on a prompt.", add_help=False
    )
    parser.add_argument("--model", type=int, default=5, help="The model ID to use.")
    parser.add_argument(
        "--refiner", action="store_true", help="Whether to use the refiner."
    )
    parser.add_argument(
        "--magic", action="store_true", help="Whether to use magic prompt."
    )

    try:
        parsed_args = parser.parse_known_args(args_list)[0]
        if not prompt:
            await ctx.message.reply("You must provide a prompt.")
            return
        image_path = generate_image(
            prompt=prompt,
            model_id=parsed_args.model,
            use_refiner=parsed_args.refiner,
            magic_prompt=parsed_args.magic,
        )
        if image_path is None:
            await ctx.message.reply("Failed to generate an image. Please try again.")
            return
        end_time = time.time()
        time_taken = end_time - start_time
        embed_title = prompt[:253] + "..." if len(prompt) > 256 else prompt
        embed = discord.Embed(title=embed_title, color=0x00FF00)
        embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
        embed.set_footer(text=f"{time_taken:.2f}s")
        await ctx.message.reply(embed=embed, file=discord.File(image_path))
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print(e)

@bot.slash_command(description="Clear messages in the current channel.")
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.respond(f"Purged {amount} messages.", delete_after=5)

@bot.slash_command(description="Clear messages in the DM.")
async def clear(ctx, amount: int):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.respond(f"Cleared {amount} messages.", delete_after=5)
    else:
        await ctx.respond("This command can only be used in DMs.")

@bot.slash_command(description="Join the voice channel of the user.")
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.respond("You are not in a voice channel.")
    else:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.respond(f"Joined {channel}.")

@bot.slash_command(description="Leave the voice channel.")
async def leave(ctx):
    if ctx.voice_client is None:
        await ctx.respond("I am not in a voice channel.")
    else:
        await ctx.voice_client.disconnect()
        await ctx.respond("Left the voice channel.")

@bot.slash_command(description="Play a song in the voice channel.")
async def play(ctx, *, song: str):
    if ctx.author.voice is None:
        await ctx.respond("You are not in a voice channel.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()

    ydl_opts = ytdl_format_options
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song, download=False)
        url2 = info["formats"][0]["url"]
        title = info["title"]

    source = discord.FFmpegPCMAudio(url2, **ffmpeg_options)

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    ctx.voice_client.play(source)
    await ctx.respond(f"Now playing: {title}")

@bot.slash_command(description="Stop the currently playing song.")
async def stop(ctx):
    if ctx.voice_client is None:
        await ctx.respond("I am not in a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.respond("Stopped playing the song.")
    else:
        await ctx.respond("No song is currently playing.")

@bot.slash_command(description="Fetch the lyrics of a song.")
async def lyrics(ctx, *, song: str):
    try:
        song_lyrics = genius.search_song(song)
        if song_lyrics:
            embed = Embed(
                title=song_lyrics.title,
                description=song_lyrics.lyrics,
                color=discord.Color.blue(),
            )
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Lyrics not found for the specified song.")
    except Exception as e:
        await ctx.respond(f"An error occurred: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
