import os, time, random, asyncio, aiohttp, json, lyricsgenius, discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
from typing import Optional
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
WOLF = os.getenv("WOLF")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

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
• Playing music and entertainment
• Weather updates and calculations
• Games and entertainment

TOOL CALLING INSTRUCTIONS:
When I need to use a tool, I should wrap the tool call in special tags:
<tool_calls>
{"name": "tool-name", "arguments": {"key": "value"}}
</tool_calls>

HOW TOOL CALLING WORKS:
1. When I decide to use a tool, I should include the tool call in my response
2. The tool will be executed automatically
3. I will be called again with the results of the tool execution
4. I should then provide a complete response that incorporates the tool results

EXAMPLE WORKFLOW:
User: "What's the weather in New York?"
My first response might include: 
<tool_calls>
{"name": "weather", "arguments": {"city": "New York"}}
</tool_calls>

Then I'll receive the tool results and generate a final comprehensive response like:
"The weather in New York is currently 72°F (22°C) with partly cloudy skies. The humidity is at 45% with a light breeze of 8 mph. It looks like a pleasant day overall!"

Available Tools:
1. Information & Utility
   • weather [city] - Current weather conditions
   • calculate [query] - Wolfram Alpha queries for:
     - Mathematical calculations (2+2, solve x^2=16, derivatives, integrals)
     - Unit conversions (100 km to miles, 50 celsius to fahrenheit)
     - Scientific data (density of gold, speed of light, periodic table info)
     - Geographic information (population of Tokyo, area of France)
     - Historical facts (when was Einstein born, World War 2 dates)
     - Astronomical data (distance to moon, sunrise time in Paris)
     - Financial data (current exchange rates, stock prices)
     - General knowledge (tallest mountain, largest ocean, capital cities)
     - Statistics and comparisons (compare GDP of countries)
     - Date/time calculations (days between dates, time zones)
   • lyrics [song] - Get song lyrics
   • whats_new - Display recent bot updates and new features

2. Entertainment & Games
   • gtn - Number guessing game
   • dice [sides] - Roll dice (default: 6)
   • flip - Flip a coin
   • ask [question] - Yes/no answers

3. Media
   • cat - Random cat image
   • dog - Random dog image
   • gt - Sends picture of GT
   • music [query] - Play music in voice channel
   • leave - Disconnect bot from voice channel

4. Management
   • purge [amount] - Delete messages
   • clear [amount] - Clear DM messages

Response Guidelines:
• Keep responses concise and natural
• Use appropriate emojis sparingly
• For errors, provide clear, friendly explanations
• Maintain context in conversations
• Format responses for readability
• When using tools, focus on incorporating tool results naturally in your final response
• For music playback, check if the user is in a voice channel first
• Use the calculate tool for ANY factual information, data, or knowledge queries - not just math!
• Examples of calculate tool usage:
  - "What's the population of Japan?" → calculate
  - "Convert 5 feet to meters" → calculate
  - "When was the iPhone first released?" → calculate
  - "What's the chemical formula for water?" → calculate
  - "Distance between Earth and Mars" → calculate
• When you receive image URLs from tools (especially calculate), include them directly in your response - Discord will automatically display the images
• Image URLs should be included on separate lines for best display

Note: Process user messages in format "username: message" but respond to message content only.
"""

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

ytdl_format_options = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": os.path.join(music_dir, "%(title)s.%(ext)s"),
    "restrictfilenames": True,
    "noplaylist": False,
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
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


async def calculate(ctx, query, from_tool_call=False):
    """Calculate using Wolfram Alpha LLM API."""
    try:
        base_url = "https://www.wolframalpha.com/api/v1/llm-api"
        params = {"input": query, "appid": WOLF, "maxchars": 2000}

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    result = await response.text()

                    # Extract image URLs from the result
                    image_urls = []
                    lines = result.split("\n")
                    for line in lines:
                        if (
                            line.strip().startswith("image: https://")
                            or line.strip().startswith("Image:")
                            and "https://" in line
                        ):
                            # Extract URL from the line
                            url_start = line.find("https://")
                            if url_start != -1:
                                url_end = line.find(" ", url_start)
                                if url_end == -1:
                                    url_end = len(line)
                                image_url = line[url_start:url_end].strip()
                                if (
                                    image_url.endswith(".png")
                                    or image_url.endswith(".jpg")
                                    or image_url.endswith(".jpeg")
                                ):
                                    image_urls.append(image_url)

                    if not from_tool_call:
                        await send_response(ctx, result)
                        # Send images if found
                        if image_urls:
                            for img_url in image_urls[:3]:  # Limit to 3 images max
                                try:
                                    embed = discord.Embed()
                                    embed.set_image(url=img_url)
                                    if hasattr(ctx, "respond"):
                                        await ctx.followup.send(embed=embed)
                                    else:
                                        await ctx.send(embed=embed)
                                except Exception as e:
                                    pass

                    # Include image URLs in the return for tool calls
                    if image_urls:
                        result += f"\n\nImages available: {', '.join(image_urls[:3])}"

                    return result
                elif response.status == 501:
                    error_msg = await response.text()
                    if not from_tool_call:
                        await send_response(ctx, f"Could not interpret query: {query}")
                    return (
                        f"Could not interpret query: {query}. Suggestions: {error_msg}"
                    )
                elif response.status == 403:
                    error_msg = "Invalid or missing Wolfram Alpha API key"
                    if not from_tool_call:
                        await send_response(ctx, error_msg)
                    return error_msg
                else:
                    error_msg = f"Wolfram Alpha API error (status {response.status})"
                    if not from_tool_call:
                        await send_response(ctx, error_msg)
                    return error_msg

    except Exception as e:
        error_msg = f"Error calculating: {str(e)}"
        if not from_tool_call:
            await send_response(ctx, "An error occurred while calculating.")
        return error_msg


async def generate_chat_completion(
    ctx: commands.Context,
    server_id: Optional[str],
    channel_id: str,
    user_id: str,
    prompt: str,
    is_tool_followup: bool = False,
) -> Optional[str]:
    """Generate a chat completion response using Gemini."""
    try:
        global conversation_memory
        context_key = server_id if server_id else f"DM-{channel_id}-{user_id}"

        if context_key not in conversation_memory:
            conversation_memory[context_key] = ConversationBufferWindowMemory(
                k=42, return_messages=True
            )

        memory = conversation_memory[context_key]

        if not gemini_client:
            await send_response(
                ctx,
                "Gemini client is not configured. Please check your GEMINI_API_KEY or GOOGLE_API_KEY.",
            )
            return None

        conversation_history = []
        system_content = system_prompt
        chat_history = memory.chat_memory.messages

        for message in chat_history:
            if hasattr(message, "content"):
                if hasattr(message, "type") and message.type == "human":
                    conversation_history.append(f"User: {message.content}")
                elif hasattr(message, "type") and message.type == "ai":
                    conversation_history.append(f"Assistant: {message.content}")

        conversation_history.append(prompt)

        full_prompt = f"{system_content}\n\nConversation:\n" + "\n".join(
            conversation_history
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=full_prompt),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=0.7,
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            response_mime_type="text/plain",
        )

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config,
        )

        response_text = response.text if hasattr(response, "text") else str(response)

        memory.chat_memory.add_user_message(prompt)
        memory.chat_memory.add_ai_message(response_text)

        return response_text

    except Exception as e:
        await send_response(ctx, "I encountered an error processing your request.")
        return None


async def handle_tool_call(
    ctx: commands.Context,
    tool_call_text: str,
    memory: ConversationBufferWindowMemory,
    send_directly: bool = False,
) -> str:
    """Handle tool calls embedded in the response."""
    try:
        start = tool_call_text.index("<tool_calls>") + len("<tool_calls>")
        end = tool_call_text.index("</tool_calls>")
        tool_call_json = tool_call_text[start:end].strip()

        try:
            tool_call = json.loads(tool_call_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid tool call format")

        tool_name = tool_call.get("name")
        tool_arguments = tool_call.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name not specified")

        tool_actions = {
            "cat": lambda: cat(ctx, from_tool_call=send_directly),
            "dog": lambda: dog(ctx, from_tool_call=send_directly),
            "gtn": lambda: gtn(ctx, from_tool_call=send_directly),
            "hello": lambda: hello(ctx, from_tool_call=send_directly),
            "dice": lambda: dice(
                ctx,
                sides=int(tool_arguments.get("sides", 6)),
                from_tool_call=send_directly,
            ),
            "flip": lambda: flip(ctx, from_tool_call=send_directly),
            "ask": lambda: ask(
                ctx,
                question=tool_arguments.get("question"),
                from_tool_call=send_directly,
            ),
            "purge": lambda: purge(
                ctx,
                amount=int(tool_arguments.get("amount", 5)),
                from_tool_call=send_directly,
            ),
            "calculate": lambda: calculate(
                ctx, query=tool_arguments.get("query"), from_tool_call=send_directly
            ),
            "weather": lambda: weather(
                ctx, city=tool_arguments.get("city"), from_tool_call=send_directly
            ),
            "gt": lambda: gt(ctx, from_tool_call=send_directly),
            "music": lambda: music_play(
                ctx, query=tool_arguments.get("query"), from_tool_call=send_directly
            ),
            "leave": lambda: music_leave(ctx, from_tool_call=send_directly),
            "whats_new": lambda: whats_new(ctx, from_tool_call=send_directly),
        }

        if tool_name not in tool_actions:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = await tool_actions[tool_name]()

        if result and memory:
            memory.chat_memory.messages[-1].content += f"\nTool result: {result}"

        return result

    except (ValueError, KeyError) as e:
        error_msg = f"Tool call error: {str(e)}"
        if not send_directly:
            await send_response(ctx, "I encountered an error with the requested tool.")
        return f"Error: {str(e)}"

    except Exception as e:
        if not send_directly:
            await send_response(ctx, "An unexpected error occurred.")
        return f"Error: {str(e)}"


statuses = [
    "Ask me anything! 💭",
    "Weather forecasts 🌤️",
    "Playing music 🎵",
    "Number guessing 🎲",
    "Rolling dice 🎯",
    "Flipping coins 🪙",
    "Managing messages 📝",
    "Fetching lyrics 🎤",
    "Calculating math 🔢",
    "Sharing knowledge 📚",
    "Running on local power 🔋",
    "Processing requests ⚡",
    "Thinking in binary 🤖",
    "Learning new tricks 🎓",
    "Here to help! 👋",
    "Chat with me 💬",
    "Ready for commands ⌨️",
    "Local assistant 🤝",
    "Online and active ✨",
    "Fast responses ⚡",
    "24/7 Service 🕒",
    "Version 4.0 🆕",
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
    if bot.user and bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(
            ctx, message=message.content.replace(f"<@{bot.user.id}>", "").strip()
        )
    else:
        await bot.process_commands(message)


@bot.slash_command(description="Send a picture of a cat.")
async def cat(ctx, from_tool_call=False):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.thecatapi.com/v1/images/search"
        ) as response:
            if response.status == 200:
                data = await response.json()
                image_url = data[0]["url"]
                if not from_tool_call:
                    await send_response(ctx, image_url)
                return image_url
            else:
                if not from_tool_call:
                    await send_response(ctx, "Failed to fetch cat image.")
                return "Failed to fetch cat image."


@bot.slash_command(description="Send a picture of a dog.")
async def dog(ctx, from_tool_call=False):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.thedogapi.com/v1/images/search"
        ) as response:
            if response.status == 200:
                data = await response.json()
                image_url = data[0]["url"]
                if not from_tool_call:
                    await send_response(ctx, image_url)
                return image_url
            else:
                if not from_tool_call:
                    await send_response(ctx, "Failed to fetch dog image.")
                return "Failed to fetch dog image."


@bot.slash_command(description="Send a picture of GT.")
async def gt(ctx, from_tool_call=False):
    image_url = "https://imgur.com/a/HlM60jA"
    if not from_tool_call:
        await send_response(ctx, image_url)
    return image_url


@bot.slash_command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx, from_tool_call=False):
    secret_number = random.randint(1, 10)
    if not from_tool_call:
        await send_response(ctx, "Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                if not from_tool_call:
                    await send_response(
                        ctx, "Congratulations! You guessed the correct number."
                    )
            else:
                if not from_tool_call:
                    await send_response(
                        ctx, f"Sorry, the correct number was {secret_number}."
                    )
            return f"Guessed number: {guess_number}\nSecret number: {secret_number}"
        else:
            if not from_tool_call:
                await send_response(ctx, "Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        if not from_tool_call:
            await send_response(ctx, "Time is up! You took too long to guess.")
        return "User timed out while guessing."


@bot.slash_command(description="Tell the user hello.")
async def hello(ctx, from_tool_call=False):
    message = f"Hello, {ctx.author.display_name}!"
    if not from_tool_call:
        await send_response(ctx, message)
    return message


@bot.slash_command(description="Roll a dice with the specified number of sides.")
async def dice(ctx, sides: int = 6, from_tool_call=False):
    result = random.randint(1, sides)
    message = f"You rolled a {result}."
    if not from_tool_call:
        await send_response(ctx, message)
    return f"Rolled a {result} on a {sides}-sided dice."


@bot.slash_command(description="Flip a coin.")
async def flip(ctx, from_tool_call=False):
    result = random.choice(["Heads", "Tails"])
    message = f"The coin landed on: **{result}**"
    if not from_tool_call:
        await send_response(ctx, message)
    return f"Coin flip result: {result}"


@bot.slash_command(description="Ask the bot a yes/no question.")
async def ask(ctx, question: str, from_tool_call=False):
    result = random.choice(["Yes", "No", "Maybe", "Definitely", "Not likely"])
    message = f"Question: {question}\nAnswer: {result}"
    if not from_tool_call:
        await send_response(ctx, message)
    return message


@bot.command(description="Chat with the bot.")
async def chat(ctx, *, message):
    async with ctx.typing():
        try:
            server_id = str(ctx.guild.id) if ctx.guild else None
            channel_id = str(ctx.channel.id)
            user_id = str(ctx.author.id)
            username = ctx.author.display_name

            message = username + ": " + message
            context_key = server_id if server_id else f"DM-{channel_id}-{user_id}"

            global conversation_memory
            if context_key not in conversation_memory:
                conversation_memory[context_key] = ConversationBufferWindowMemory(
                    k=42, return_messages=True
                )

            memory = conversation_memory[context_key]

            response = await generate_chat_completion(
                ctx=ctx,
                prompt=message,
                server_id=server_id,
                channel_id=channel_id,
                user_id=user_id,
            )

            tool_was_used = False
            if response:
                while "<tool_calls>" in response and "</tool_calls>" in response:
                    tool_was_used = True

                    tool_start = response.find("<tool_calls>")
                    tool_end = response.find("</tool_calls>") + len("</tool_calls>")
                    tool_call_text = response[tool_start:tool_end]

                    pre_tool_text = response[:tool_start].strip()
                    if pre_tool_text:

                        first_tool_call = not any(
                            "<tool_calls>" in msg.content
                            for msg in memory.chat_memory.messages
                            if hasattr(msg, "content")
                        )
                        if first_tool_call:
                            await ctx.reply(pre_tool_text)

                    tool_result = await handle_tool_call(
                        ctx,
                        tool_call_text,
                        memory,
                        send_directly=True,
                    )

                    remaining_text = response[tool_end:].strip()

                    if "<tool_calls>" in remaining_text:

                        response = remaining_text
                    else:

                        followup_prompt = (
                            f"You used one or more tools to answer the user's question. "
                            f"The last tool result was: {tool_result}. "
                            f"Please provide a complete response that incorporates all information "
                            f"and answers the original question fully. Do not use any more tool calls."
                        )

                        followup_response = await generate_chat_completion(
                            ctx=ctx,
                            prompt=username + ": " + followup_prompt,
                            server_id=server_id,
                            channel_id=channel_id,
                            user_id=user_id,
                            is_tool_followup=True,
                        )

                        await send_complete_response(ctx, followup_response)
                        break

            if not tool_was_used:
                await send_complete_response(ctx, response)

        except Exception as e:
            await send_response(ctx, f"An error occurred: {e}")


async def send_complete_response(ctx, response):
    """Send a complete response, handling message size limits."""
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


@bot.slash_command(description="Delete a set number of messages.")
async def purge(ctx, amount: int, from_tool_call=False):
    await ctx.channel.purge(limit=amount + 1)
    if not from_tool_call:
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
        discord.FFmpegPCMAudio(
            filename,
            before_options=ffmpeg_options["before_options"],
            options=ffmpeg_options["options"],
        ),
        after=lambda e: bot.loop.create_task(after_playback(e, ctx)),
    )
    await ctx.followup.send(f'Now playing: {info["title"]}')


@bot.slash_command(description="Play a song or playlist from YouTube.")
async def play(ctx, *, query):

    if not ctx.author.voice:
        await ctx.response.send_message(
            "You need to be in a voice channel to play music.", ephemeral=True
        )
        return

    state = await get_server_state(ctx.guild.id)

    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.response.defer()
    else:

        if ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.disconnect()
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.response.defer()
        else:
            await ctx.response.defer()

    ydl = youtube_dl.YoutubeDL(ytdl_format_options)

    if "http" in query:
        url = query
    else:
        url = f"ytsearch:{query}"
    try:
        info = ydl.extract_info(url, download=True)
        if info and "entries" in info:
            for entry in info["entries"]:
                filename = ydl.prepare_filename(entry)
                state["playlist_queue"].append({"info": entry, "filename": filename})
        elif info:
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
async def lyrics(ctx, *, song_name: Optional[str] = None):
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


async def weather(ctx, city: str, from_tool_call: bool = False) -> str:
    """Get current weather for a city using OpenWeatherMap API."""
    try:

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&units=metric&appid={WEATHER_API_KEY}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url) as response:
                if response.status != 200:
                    if response.status == 404:
                        error_msg = f"Could not find city: {city}"
                        if not from_tool_call:
                            await send_response(ctx, error_msg)
                        return error_msg
                    raise Exception(f"Weather API error: {response.status}")

                data = await response.json()

                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                weather_desc = data["weather"][0]["description"]
                pressure = data["main"]["pressure"]

                location_name = f"{data['name']}, {data['sys']['country']}"

                weather_id = data["weather"][0]["id"]
                weather_emoji = "🌈"  # default
                if weather_id < 300:
                    weather_emoji = "⛈️"  # thunderstorm
                elif weather_id < 400:
                    weather_emoji = "🌧️"  # drizzle
                elif weather_id < 500:
                    weather_emoji = "🌧️"  # rain
                elif weather_id < 600:
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

                if not from_tool_call:
                    await send_response(ctx, response)
                return response

    except Exception as e:
        error_msg = f"Error fetching weather: {str(e)}"
        print(error_msg)
        if not from_tool_call:
            await send_response(ctx, "Sorry, I couldn't fetch the weather information.")
        return error_msg


@bot.slash_command(description="Get current weather for a city.")
async def getweather(ctx, *, city: str):
    await weather(ctx, city)


async def music_play(ctx, query: str, from_tool_call: bool = False) -> str:
    """Play music in a voice channel via the chat interface."""
    try:

        if not ctx.author.voice:
            message = "You need to be in a voice channel to play music."
            if not from_tool_call:
                await ctx.reply(message)
            return message

        state = await get_server_state(ctx.guild.id)

        if not ctx.voice_client:
            channel = ctx.author.voice.channel
            try:
                await channel.connect()
            except discord.errors.ClientException as e:
                error_msg = f"Couldn't connect to voice channel: {str(e)}"
                if not from_tool_call:
                    await ctx.reply(error_msg)
                return error_msg
        else:

            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.disconnect()
                channel = ctx.author.voice.channel
                try:
                    await channel.connect()
                except discord.errors.ClientException as e:
                    error_msg = f"Couldn't connect to voice channel: {str(e)}"
                    if not from_tool_call:
                        await ctx.reply(error_msg)
                    return error_msg

        ydl = youtube_dl.YoutubeDL(ytdl_format_options)

        if "http" in query:
            url = query
        else:
            url = f"ytsearch:{query}"

        status_message = f"Searching for '{query}'..."
        if not from_tool_call:
            await ctx.reply(status_message)

        try:

            info = ydl.extract_info(url, download=True)
            result = "No songs found."

            if info and "entries" in info:

                songs_added = 0
                for entry in info["entries"]:
                    filename = ydl.prepare_filename(entry)
                    state["playlist_queue"].append(
                        {"info": entry, "filename": filename}
                    )
                    songs_added += 1
                result = f"Added {songs_added} songs to the queue from playlist."
            elif info:

                filename = ydl.prepare_filename(info)
                state["playlist_queue"].append({"info": info, "filename": filename})
                result = f"Added '{info['title']}' to the queue."

            if not state["current_song"] and state["playlist_queue"]:
                next_song = state["playlist_queue"].pop(0)
                title = next_song["info"]["title"]

                await ctx.send(f"Now playing: {title}")

                ctx.voice_client.play(
                    discord.FFmpegPCMAudio(
                        next_song["filename"],
                        before_options=ffmpeg_options["before_options"],
                        options=ffmpeg_options["options"],
                    ),
                    after=lambda e: bot.loop.create_task(after_playback(e, ctx)),
                )

                state["current_song"] = next_song
                result = f"Now playing: {title}"

            return result

        except Exception as e:
            error_message = f"Error: {str(e)}"
            if not from_tool_call:
                await ctx.reply(error_message)
            return error_message

    except Exception as e:
        error_message = f"Failed to play music: {str(e)}"
        if not from_tool_call:
            await ctx.reply(error_message)
        return error_message


async def music_leave(ctx, from_tool_call: bool = False) -> str:
    """Leave the voice channel via the chat interface."""
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            message = "I've left the voice channel."
            if not from_tool_call:
                await ctx.reply(message)
            return message
        else:
            message = "I'm not in a voice channel."
            if not from_tool_call:
                await ctx.reply(message)
            return message
    except Exception as e:
        error_message = f"Failed to leave voice channel: {str(e)}"
        if not from_tool_call:
            await ctx.reply(error_message)
        return error_message


async def whats_new(ctx, from_tool_call=False):
    """Read the whatsnew.md file and tell users what's new."""
    try:
        whatsnew_path = os.path.join(os.path.dirname(__file__), "whatsnew.md")

        if not os.path.exists(whatsnew_path):
            message = "The What's New file couldn't be found. Please check with the bot administrator."
            if not from_tool_call:
                await ctx.reply(message)
            return message

        with open(whatsnew_path, "r") as file:
            content = file.read()

        if len(content) > 1900:
            content = content[:1900] + "\n\n... (truncated)"

        message = f"**What's New in LocalBot**\n\n{content}"

        if not from_tool_call:
            await ctx.reply(message)
        return message
    except Exception as e:
        error_message = f"Error reading What's New information: {str(e)}"
        if not from_tool_call:
            await ctx.reply(error_message)
        return error_message


bot.run(TOKEN)
