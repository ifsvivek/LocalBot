import os, time, random, asyncio, aiohttp, json, lyricsgenius, discord, base64, wolframalpha
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
from PIL import Image
from io import BytesIO
from typing import Union, Optional
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
WOLF = os.getenv("WOLF")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

music_dir = "music"
os.makedirs(music_dir, exist_ok=True)
genius = lyricsgenius.Genius(GENIUS_TOKEN)
current_song = None
playlist_queue = []
server_state = {}
conversation_memory = {}
system_prompt = """
System: I am LocalBot, a helpful discord bot focused on providing a natural and engaging experience.

My core abilities include:
• Casual conversation with emojis (used moderately)
• Generating images and playing music
• Weather updates and calculations
• Games and entertainment

When I need to use a tool, I use this format:
<tool_call>
{"name": "tool-name", "arguments": {"key": "value"}}
</tool_call>

Available Tools:
1. Information & Utility
   • /weather [city] - Current weather conditions
   • /calculate [query] - Math, time, date, general knowledge
   • /lyrics [song] - Get song lyrics

2. Entertainment & Games
   • /imagine [prompt] - Generate images
   • /gtn - Number guessing game
   • /dice [sides] - Roll dice (default: 6)
   • /flip - Flip a coin
   • /ask [question] - Yes/no answers

3. Media
   • /cat - Random cat image
   • /dog - Random dog image
   • /gt - Sends picture of GT

4. Management
   • /purge [amount] - Delete messages
   • /clear [amount] - Clear DM messages

Response Guidelines:
• Keep responses concise and natural
• Use appropriate emojis sparingly
• For errors, provide clear, friendly explanations
• Maintain context in conversations
• Format responses for readability

Note: Process user messages in format "username: message" but respond to message content only.
"""

groq_api_key = os.environ.get("GROQ_API_KEY")
model_name = "llama-3.2-90b-vision-preview"
groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)

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


async def send_response(ctx, message):
    if hasattr(ctx, "respond"):
        await ctx.respond(message)
    else:
        await ctx.reply(message)
    return message


def random_bright_color():
    def bright_value():
        return random.randint(128, 255)

    return "#{:02X}{:02X}{:02X}".format(bright_value(), bright_value(), bright_value())


async def calculate(ctx, query):
    client = wolframalpha.Client(WOLF)
    loop = asyncio.get_running_loop()
    try:
        res = await loop.run_in_executor(None, client.query, query)
        result_texts = []
        image_links = []
        for pod in res.pods:
            if "subpod" in pod:
                subpods = (
                    pod["subpod"]
                    if isinstance(pod["subpod"], list)
                    else [pod["subpod"]]
                )
                for subpod in subpods:
                    if "plaintext" in subpod and subpod["plaintext"]:
                        result_texts.append(subpod["plaintext"])
                    if "img" in subpod and "@src" in subpod["img"]:
                        image_links.append(subpod["img"]["@src"])
        if result_texts:
            await send_response(ctx, result_texts[1])
        return json.dumps({"results": result_texts, "images": image_links})
    except Exception as e:
        print(f"An error occurred: {e}")
        await send_response(ctx, "An error occurred while fetching the result.")


async def generate_chat_completion(
    ctx: commands.Context,
    server_id: Optional[str],
    channel_id: str,
    user_id: str,
    prompt: str,
) -> Optional[str]:
    """Generate a chat completion response."""
    try:
        context_key = server_id if server_id else f"DM-{channel_id}-{user_id}"

        # Initialize or get existing memory
        if not hasattr(generate_chat_completion, "conversation_memory"):
            generate_chat_completion.conversation_memory = {}

        if context_key not in generate_chat_completion.conversation_memory:
            generate_chat_completion.conversation_memory[context_key] = (
                ConversationBufferWindowMemory(
                    k=10, memory_key="chat_history", return_messages=True
                )
            )

        memory = generate_chat_completion.conversation_memory[context_key]

        # Create prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{human_input}"),
            ]
        )

        # Initialize conversation chain
        conversation = LLMChain(
            llm=groq_chat, prompt=prompt_template, memory=memory, verbose=False
        )

        # Generate response
        response = await asyncio.to_thread(conversation.predict, human_input=prompt)

        # Handle tool calls if present
        if "<tool_call>" in response and "</tool_call>" in response:
            response = await handle_tool_call(ctx, response, memory)

        return response

    except Exception as e:
        print(f"Chat completion error: {str(e)}")
        await send_response(ctx, "I encountered an error processing your request.")
        return None


async def handle_tool_call(
    ctx: commands.Context, response: str, memory: ConversationBufferWindowMemory
) -> str:
    """Handle tool calls embedded in the response."""
    try:
        # Extract tool call
        start = response.index("<tool_call>") + len("<tool_call>")
        end = response.index("</tool_call>")
        tool_call_json = response[start:end].strip()

        # Parse tool call
        try:
            tool_call = json.loads(tool_call_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid tool call format")

        tool_name = tool_call.get("name")
        tool_arguments = tool_call.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name not specified")

        # Define available tools with type hints
        tool_actions = {
            "imagine": lambda: imagine(ctx, prompt=tool_arguments.get("prompt")),
            "cat": lambda: cat(ctx),
            "dog": lambda: dog(ctx),
            "gtn": lambda: gtn(ctx),
            "hello": lambda: hello(ctx),
            "dice": lambda: dice(ctx, sides=int(tool_arguments.get("sides", 6))),
            "flip": lambda: flip(ctx),
            "ask": lambda: ask(ctx, question=tool_arguments.get("question")),
            "purge": lambda: purge(ctx, amount=int(tool_arguments.get("amount", 5))),
            "calculate": lambda: calculate(ctx, query=tool_arguments.get("query")),
            "weather": lambda: weather(ctx, city=tool_arguments.get("city")),
            "gt": lambda: gt(ctx),
        }

        # Execute tool
        if tool_name not in tool_actions:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = await tool_actions[tool_name]()

        # Update memory with tool result
        if result:
            memory.chat_memory.messages[-1].content += f"\nTool result: {result}"

        return memory.chat_memory.messages[-1].content

    except (ValueError, KeyError) as e:
        error_msg = f"Tool call error: {str(e)}"
        print(error_msg)
        await send_response(ctx, "I encountered an error with the requested tool.")
        return response

    except Exception as e:
        print(f"Unexpected tool error: {str(e)}")
        await send_response(ctx, "An unexpected error occurred.")
        return response


async def generate_image(prompt: str) -> Optional[str]:
    output_dir = "img"
    os.makedirs(output_dir, exist_ok=True)

    url = "https://sd.ifsvivek.in/sdapi/v1/txt2img"

    params = {"prompt": prompt, "steps": 50, "sampler_index": "DPM++ 2M"}

    async with aiohttp.ClientSession() as session:

        async with session.post(url, json=params) as response:
            if response.status == 200:

                data = await response.json()
                image_data = data.get("images", [])[0]

                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
                timestamp = int(time.time())
                image_path = os.path.join(output_dir, f"img_{timestamp}.png")
                try:
                    image.save(image_path)
                    return image_path
                except Exception as e:
                    print(f"Error saving image: {e}")
                    return None
            else:
                print(f"Error: Received status code {response.status}")
                return None


statuses = [
    # Interactive Features
    "Ask me anything! 💭",
    "Creating AI art 🎨",
    "Weather forecasts 🌤️",
    "Playing music 🎵",
    # Games
    "Number guessing 🎲",
    "Rolling dice 🎯",
    "Flipping coins 🪙",
    # Helper Features
    "Managing messages 📝",
    "Fetching lyrics 🎤",
    "Calculating math 🔢",
    "Sharing knowledge 📚",
    # Fun Statuses
    "Running on local power 🔋",
    "Processing requests ⚡",
    "Thinking in binary 🤖",
    "Learning new tricks 🎓",
    # Friendly Messages
    "Here to help! 👋",
    "Chat with me 💬",
    "Ready for commands ⌨️",
    "Local assistant 🤝",
    # System Status
    "Online and active ✨",
    "Fast responses ⚡",
    "24/7 Service 🕒",
    "Version 3.0 🆕",
]


@tasks.loop(minutes=1.0)
async def change_status(bot):
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    change_status.start(bot)


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
                image_url = data[0]["url"]
                await send_response(ctx, image_url)
                return image_url
            else:
                await send_response(ctx, "Failed to fetch cat image.")


@bot.slash_command(description="Send a picture of a dog.")
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.thedogapi.com/v1/images/search"
        ) as response:
            if response.status == 200:
                data = await response.json()
                image_url = data[0]["url"]
                await send_response(ctx, image_url)
                return image_url
            else:
                await send_response(ctx, "Failed to fetch dog image.")


@bot.slash_command(description="Send a picture of GT.")
async def gt(ctx):
    await send_response(ctx, "https://imgur.com/a/HlM60jA")
    return "https://imgur.com/a/HlM60jA"


@bot.slash_command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    await send_response(ctx, "Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                await send_response(
                    ctx, "Congratulations! You guessed the correct number."
                )
            else:
                await send_response(
                    ctx, f"Sorry, the correct number was {secret_number}."
                )
            return f"Guessed number: {guess_number}\nSecret number: {secret_number}"
        else:
            await send_response(ctx, "Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        await send_response(ctx, "Time is up! You took too long to guess.")


@bot.slash_command(description="Tell the user hello.")
async def hello(ctx):
    await send_response(ctx, f"Hello, {ctx.author.display_name}!")
    return f"Hello, {ctx.author.display_name}!"


@bot.slash_command(description="Roll a dice with the specified number of sides.")
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await send_response(ctx, f"You rolled a {result}.")
    return f"Rolled a {result} on a {sides}-sided dice."


@bot.slash_command(description="Flip a coin.")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await send_response(ctx, f"The coin landed on: **{result}**")
    return f"Coin flip result: {result}"


@bot.slash_command(description="Ask the bot a yes/no question.")
async def ask(ctx, question: str):
    result = random.choice(["Yes", "No", "Maybe", "Definitely", "Not likely"])
    await send_response(ctx, f"Question: {question}\nAnswer: {result}")
    return f"Question: {question}\nAnswer: {result}"


@bot.command(description="Chat with the bot.")
async def chat(ctx, *, message):
    async with ctx.typing():
        try:
            server_id = str(ctx.guild.id) if ctx.guild else None
            channel_id = str(ctx.channel.id)
            user_id = str(ctx.author.id)
            username = ctx.author.display_name

            message = username + ": " + message

            response = await generate_chat_completion(
                ctx=ctx,
                prompt=message,
                server_id=server_id,
                channel_id=channel_id,
                user_id=user_id,
            )

            if "<tool_call>" in response:
                return

            if len(response) > 2000:
                is_first_chunk = True
                while response:
                    split_at = (response[:2000].rfind("\n") + 1) or 2000
                    chunk, response = (
                        response[:split_at].strip(),
                        response[split_at:].trip(),
                    )
                    if is_first_chunk:
                        await ctx.reply(chunk)
                        is_first_chunk = False
                    else:
                        await ctx.send(chunk)
            else:
                await ctx.reply(response)

        except Exception as e:
            await send_response(ctx, f"An error occurred: {e}")


@bot.slash_command(description="Generate an image based on a prompt.")
async def imagine(ctx, *, prompt: str) -> None:
    async def send_initial_message():
        if hasattr(ctx, "respond"):
            return await ctx.respond("Generating image, please wait...")
        else:
            return await ctx.reply("Generating image, please wait...")

    async def edit_message(initial_message, content=None, embed=None, file=None):
        if hasattr(ctx, "respond"):
            await initial_message.edit(content=content, embed=embed, file=file)
        else:
            await initial_message.edit(content=content, embed=embed, file=file)

    try:
        start_time = time.time()
        initial_message = await send_initial_message()
        image_path = await generate_image(prompt)
        time_taken = time.time() - start_time

        if image_path:
            embed_title = prompt[:253] + "..." if len(prompt) > 256 else prompt
            embed = discord.Embed(
                title=embed_title, color=int(random_bright_color()[1:], 16)
            )
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            embed.set_footer(text=f"Time taken: {time_taken:.2f}s")
            await edit_message(
                initial_message,
                content=None,
                embed=embed,
                file=discord.File(image_path),
            )
            if os.path.exists(image_path):
                os.remove(image_path)
        else:
            await edit_message(initial_message, content="Failed to generate image.")
    except Exception as e:
        print(f"Error generating image: {e}")
        if hasattr(ctx, "respond"):
            await ctx.respond("An error occurred while generating the image.")
        else:
            await ctx.reply("An error occurred while generating the image.")


@bot.slash_command(description="Delete a set number of messages.")
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await send_response(ctx, f"Deleted {amount} messages.")
    return f"Deleted {amount} messages."


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
        await send_response(ctx, "This command can only be used in direct messages.")


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
        os.remove(state["current_song"]["filename"])
    if err:
        print(f"Playback error: {err}")
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
        try:
            await play_song(ctx, next_song["info"], next_song["filename"])
            state["current_song"] = next_song
        except Exception as e:
            await ctx.followup.send(f"Error playing song: {str(e)}")


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
            if len(lyrics) > 2000:
                for i in range(0, len(lyrics), 2000):
                    await ctx.followup.send(lyrics[i : i + 2000])
            else:
                await ctx.followup.send(lyrics)
        else:
            await ctx.followup.send(f"Lyrics for '{search_title}' not found.")
    except Exception as e:
        await ctx.followup.send(f"Error: {str(e)}")


@bot.command(description="Clear the conversation history.")
async def clear_history(ctx):
    if ctx.author.id == 471320666075824134:
        global conversation_memory
        conversation_memory.clear()
        await ctx.send("Conversation history cleared.")
    else:
        await ctx.send("You do not have permission to clear the conversation history.")


@bot.command(description="Pin a replied message.")
async def pin(ctx):
    if ctx.message.reference:
        referenced_message = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )
        await referenced_message.pin()
        await ctx.send("Message pinned successfully.")
    else:
        await ctx.send("Please reply to the message you want to pin.")


async def weather(ctx, city: str) -> str:
    """Get current weather for a city using OpenWeatherMap API."""
    try:
        # Use direct city query instead of geocoding
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&units=metric&appid={WEATHER_API_KEY}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url) as response:
                if response.status != 200:
                    if response.status == 404:
                        await send_response(ctx, f"Could not find city: {city}")
                        return f"City not found: {city}"
                    raise Exception(f"Weather API error: {response.status}")

                data = await response.json()

                # Extract weather data
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                weather_desc = data["weather"][0]["description"]
                pressure = data["main"]["pressure"]

                # Get country code and combine with city name
                location_name = f"{data['name']}, {data['sys']['country']}"

                # Select weather emoji based on weather condition code
                weather_id = data["weather"][0]["id"]
                weather_emoji = "🌈"  # default
                if weather_id < 300:
                    weather_emoji = "⛈️"  # thunderstorm
                elif weather_id < 400:
                    weather_emoji = "🌧️"  # drizzle
                elif weather_id < 600:
                    weather_emoji = "🌧️"  # rain
                elif weather_id < 700:
                    weather_emoji = "🌨️"  # snow
                elif weather_id < 800:
                    weather_emoji = "🌫️"  # atmosphere
                elif weather_id == 800:
                    weather_emoji = "☀️"  # clear
                elif weather_id <= 804:
                    weather_emoji = "☁️"  # clouds

                response = (
                    f"{weather_emoji} Weather in **{location_name}**:\n"
                    f"🌡️ Temperature: {temp:.1f}°C\n"
                    f"🤔 Feels like: {feels_like:.1f}°C\n"
                    f"💧 Humidity: {humidity}%\n"
                    f"💨 Wind speed: {wind_speed} m/s\n"
                    f"🌍 Pressure: {pressure} hPa\n"
                    f"☁️ Conditions: {weather_desc.capitalize()}"
                )

                await send_response(ctx, response)
                return response

    except Exception as e:
        error_msg = f"Error fetching weather: {str(e)}"
        print(error_msg)
        await send_response(ctx, "Sorry, I couldn't fetch the weather information.")
        return error_msg


@bot.slash_command(description="Get current weather for a city.")
async def getweather(ctx, *, city: str):
    await weather(ctx, city)


bot.run(TOKEN)
