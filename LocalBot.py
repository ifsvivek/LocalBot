import discord, random, asyncio, os, base64, argparse, time, lyricsgenius
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed
import aiohttp
from PIL import Image
from io import BytesIO
import yt_dlp as youtube_dl
from typing import Union, Optional


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


async def generate_text(
    server_id: str, channel_id: str, user_id: str, prompt: str, user_name: str
) -> Union[str, None]:
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
    conversation_history[server_id][channel_id][user_id].append(
        f"{user_name}: {prompt}"
    )

    # Optionally append the system prompt to the conversation history
    if system_prompt:
        conversation_history[server_id][channel_id][user_id].append(
            f"System: {system_prompt}"
        )

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
                conversation_history[server_id][channel_id][user_id].append(
                    f"Bot: {result['response']}"
                )
                return result["response"]
            else:
                return f"Error: Request failed with status code {response.status}"


async def generate_image(
    prompt: str,
    model_id: int = 0,
    use_refiner: bool = False,
    magic_prompt: bool = False,
    calc_metrics: bool = False,
) -> Optional[str]:
    """
    Generate an image based on the given prompt using an asynchronous API request.

    Args:
        prompt (str): The prompt for the image generation.
        model_id (int, optional): The model ID to use. Defaults to 0.
        use_refiner (bool, optional): Whether to use the refiner. Defaults to False.
        magic_prompt (bool, optional): Whether to use the magic prompt. Defaults to False.
        calc_metrics (bool, optional): Whether to calculate metrics. Defaults to False.

    Returns:
        Optional[str]: The path to the saved image, or None if the request failed.
    """
    output_dir = "img"
    os.makedirs(output_dir, exist_ok=True)

    url = "https://diffusion.ayushmanmuduli.com/gen"
    params = {
        "prompt": prompt,
        "model_id": model_id,
        "use_refiner": int(use_refiner),
        "magic_prompt": int(magic_prompt),
        "calc_metrics": int(calc_metrics),
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
        async with session.get(
            "https://api.thecatapi.com/v1/images/search"
        ) as response:
            if response.status == 200:
                data = await response.json()
                cat_image_link = data[0]["url"]
                await ctx.respond(cat_image_link)
            else:
                await ctx.respond(
                    "Failed to fetch cat image. Try again later.", ephemeral=True
                )


@bot.slash_command(description="Send a picture of a dog.")
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.thedogapi.com/v1/images/search"
        ) as response:
            if response.status == 200:
                data = await response.json()
                dog_image_link = data[0]["url"]
                await ctx.respond(dog_image_link)
            else:
                await ctx.respond(
                    "Failed to fetch dog image. Try again later.", ephemeral=True
                )


@bot.slash_command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    print("Secret Number:", secret_number)
    await ctx.respond("Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                await ctx.respond("You guessed it!")
            else:
                await ctx.respond("Nope, try again.")
        else:
            await ctx.respond("Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        await ctx.respond("Time is up! You took too long to guess.")


@bot.slash_command(description="Tell the user hello.")
async def hello(ctx):
    await ctx.respond(f"Hello, {ctx.author.name}!")


@bot.slash_command(description="Roll a dice with the specified number of sides.")
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.respond(f"You rolled a {result}.")


@bot.slash_command(description="Flip a coin.")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.respond(f"The coin landed on: **{result}**")


@bot.slash_command(description="Ask the bot a yes/no question.")
async def ask(ctx):
    result = random.choice(["Yes", "No"])
    await ctx.respond(result)


@bot.command(description="Chat with the bot.")
async def chat(ctx, *, message):
    async with ctx.typing():
        try:
            server_id = str(ctx.guild.id)
            channel_id = str(ctx.channel.id)
            user_id = str(ctx.author.id)
            user_name = ctx.author.name
            prompt = message

            response = await generate_text(
                server_id, channel_id, user_id, prompt, user_name
            )

            is_first_chunk = True
            while response:
                # Determine where to split the message
                split_at = response.rfind("\n", 0, 2000)
                if split_at == -1 or split_at > 2000:
                    split_at = 2000
                chunk = response[:split_at].strip()
                response = response[split_at:].strip()

                # Send the message in chunks to avoid hitting the character limit
                if is_first_chunk:
                    await ctx.message.reply(chunk)
                    is_first_chunk = False
                else:
                    await ctx.send(chunk)
        except Exception as e:
            print(e)


@bot.command(description="Generate an image based on a prompt.")
async def imagine(ctx, *, args):
    start_time = time.time()

    flag_index = args.find(" --")
    if flag_index != -1:
        prompt = args[:flag_index]
        args_list = args[flag_index + 1 :].split()
    else:
        prompt = args
        args_list = []

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

        image_path = await generate_image(
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


@bot.slash_command(description="Delete a set number of messages.")
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.respond(f"Deleted {amount} messages.")


@bot.command(description="Delete a set number of bot messages in DM")
async def clear(ctx, amount: int = 5):
    if isinstance(ctx.channel, discord.DMChannel):
        messages = await ctx.channel.history(limit=amount).flatten()
        bot_messages = [msg for msg in messages if msg.author == bot.user]
        for msg in bot_messages:
            await msg.delete()
        confirmation_msg = await ctx.send(f"Deleted {len(bot_messages)} messages.")
        await asyncio.sleep(5)
        await confirmation_msg.delete()
    else:
        await ctx.respond("This command can only be used in direct messages.")


@bot.command(description="List all the commands available.")
async def lc(ctx):
    embed = Embed(
        title="Available Commands",
        description="List of all commands and their descriptions.",
        color=0x00FF00,
    )

    # Add commands as fields
    embed.add_field(
        name="`/cat` or `$cat`", value="Sends a random cat image.", inline=False
    )
    embed.add_field(
        name="`/dog` or `$dog`", value="Sends a random dog image.", inline=False
    )
    embed.add_field(
        name="`/gtn` or `$gtn`", value="Starts a number guessing game.", inline=False
    )
    embed.add_field(name="`/hello` or `$hello`", value="Greets the user.", inline=False)
    embed.add_field(
        name="`/dice [sides]` or `$dice [sides]`",
        value="Rolls a dice with the specified number of sides. Default is 6 sides if none specified.",
        inline=False,
    )
    embed.add_field(name="`/flip` or `$flip`", value="Flips a coin.", inline=False)
    embed.add_field(
        name="`/ask` or `$ask`",
        value="Provides a yes/no response randomly.",
        inline=False,
    )
    embed.add_field(
        name="`/chat [message]` or `$chat [message]`",
        value="Engages in a chat with the bot using the text-generation model.",
        inline=False,
    )
    embed.add_field(
        name="`$imagine [prompt]`",
        value="Generates an image based on the provided prompt. `--magic`: Uses a magic prompt. `--model`: Specify the model to use for image generation. Range: [0, 1, 2, 3, 4].",
        inline=False,
    )
    embed.add_field(
        name="`/purge [amount]` or `$purge [amount]`",
        value="Deletes the specified number of messages in the channel. Requires the `Manage Messages` permission.",
        inline=False,
    )
    embed.add_field(
        name="`$clear [amount]`",
        value="Clears the specified number of messages in the DM.",
        inline=False,
    )
    embed.add_field(
        name="`$lc`",
        value="Lists all the available commands and their descriptions.",
        inline=False,
    )
    embed.add_field(
        name="`/join` or `$join`",
        value="Joins the voice channel of the user.",
        inline=False,
    )
    embed.add_field(
        name="`/leave` or `$leave`",
        value="Leaves the voice channel.",
        inline=False,
    )
    embed.add_field(
        name="`/play [query]` or `$play [query]`",
        value="Plays a song from YouTube in the voice channel.",
        inline=False,
    )
    embed.add_field(
        name="`/stop` or `$stop`",
        value="Stops the current playback in the voice channel.",
        inline=False,
    )
    embed.add_field(
        name="`/lyrics` or `$lyrics`",
        value="Fetches the lyrics for the current song playing in the voice channel.",
        inline=False,
    )

    await ctx.message.reply(embed=embed)


@bot.slash_command(description="Join the voice channel.")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.response.send_message("Joined the voice channel.")
    else:
        await ctx.response.send_message(
            "You are not in a voice channel!", ephemeral=True
        )


@bot.slash_command(description="Leave the voice channel.")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.response.send_message("Left the voice channel.")
    else:
        await ctx.response.send_message("I'm not in a voice channel!", ephemeral=True)


async def after_playback(err, ctx):
    state = await get_server_state(ctx.guild.id)

    if os.path.exists(state["current_song"]["filename"]):
        os.remove(state["current_song"]["filename"])  # Delete the file after playback
    if err:
        print(f"Error: {err}")

    if state["playlist_queue"]:
        next_song = state["playlist_queue"].pop(0)
        await play_song(ctx, next_song["info"], next_song["filename"])
    else:
        state["current_song"] = None


async def play_song(ctx, info, filename):
    state = await get_server_state(ctx.guild.id)
    state["current_song"] = {"title": info["title"], "filename": filename}
    ctx.voice_client.play(
        discord.FFmpegPCMAudio(filename, **ffmpeg_options),
        after=lambda e: bot.loop.create_task(after_playback(e, ctx)),
    )
    await ctx.followup.send(f'Now playing: {info["title"]}')


@bot.slash_command(description="Play a song or playlist from YouTube.")
async def play(ctx, *, query):
    state = await get_server_state(ctx.guild.id)

    if not ctx.voice_client:
        await join(ctx)

    ydl = youtube_dl.YoutubeDL(ytdl_format_options)

    if "http" in query:
        url = query
    else:
        url = f"ytsearch:{query}"

    try:
        info = ydl.extract_info(url, download=True)

        # If it's a playlist, queue all entries
        if "entries" in info:
            for entry in info["entries"]:
                filename = ydl.prepare_filename(entry)
                state["playlist_queue"].append({"info": entry, "filename": filename})
        else:
            filename = ydl.prepare_filename(info)
            state["playlist_queue"].append({"info": info, "filename": filename})

    except Exception as e:
        await ctx.followup.send(f"Error: {str(e)}")
        return

    if not state["current_song"]:
        next_song = state["playlist_queue"].pop(0)
        await play_song(ctx, next_song["info"], next_song["filename"])


@bot.slash_command(description="Stop the current playback.")
async def stop(ctx):
    state = await get_server_state(ctx.guild.id)
    ctx.voice_client.stop()
    state["current_song"] = None
    state["playlist_queue"] = []
    await ctx.response.send_message("Playback stopped.")


@bot.slash_command(description="Get lyrics for the current song or a specified song.")
async def lyrics(ctx, *, song_name: str = None):
    state = await get_server_state(ctx.guild.id)
    await ctx.response.defer()

    # Use the provided song name or the title of the current playing song
    search_title = (
        song_name
        if song_name
        else state["current_song"]["title"] if state["current_song"] else None
    )

    if not search_title:
        await ctx.followup.send(
            "No song is currently playing and no song name was provided."
        )
        return

    try:
        song = genius.search_song(search_title)
        if song:
            lyrics = song.lyrics
            # Discord has a character limit for messages (2000 characters), so split if necessary
            if len(lyrics) > 2000:
                for i in range(0, len(lyrics), 2000):
                    await ctx.followup.send(lyrics[i : i + 2000])
            else:
                await ctx.followup.send(lyrics)
        else:
            await ctx.followup.send(f"Lyrics for '{search_title}' not found.")
    except Exception as e:
        await ctx.followup.send(f"Error: {str(e)}")


bot.run(TOKEN)
