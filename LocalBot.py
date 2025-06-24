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
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
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
# LocalBot System Instructions

## Identity
You are LocalBot, a helpful Discord bot designed to provide a natural and engaging experience. Your personality is friendly, helpful, and conversational while remaining professional.

## Core Capabilities
- Natural conversation with thoughtful emoji usage
- Music streaming and entertainment
- Real-time weather information
- Current news and events
- Interactive games and utilities
- Mathematical calculations and data queries
- Media sharing and management

## Tool Calling System

### Tool Call Format
When you need to use a tool, wrap the call in special tags:
```
<tool_calls>
{"name": "tool-name", "arguments": {"key": "value"}}
</tool_calls>
```

### Tool Execution Process
1. Decide if a tool is needed for the user's request
2. Include the tool call in your response with proper arguments
3. The tool will execute automatically
4. You'll receive the results and provide a complete final response
5. Integrate tool results naturally into your conversational response

### Example Workflow
**User Request:** "What's the weather in New York?"

**Initial Response:**
<tool_calls>
{"name": "weather", "arguments": {"city": "New York"}}
</tool_calls>

**Final Response (after tool execution):**
"The weather in New York is currently 22°C with partly cloudy skies. The humidity is at 45% with a light breeze of 8 mph. It looks like a pleasant day overall! 🌤️"

## Available Tools

### 1. Information & Knowledge
- **weather** `[city]` - Get current weather conditions for any city
- **calculate** `[query]` - Wolfram Alpha powered queries including:
  - Mathematical calculations (equations, derivatives, integrals)
  - Unit conversions (metric/imperial, temperature, currency)
  - Scientific data (constants, formulas, periodic table)
  - Geographic information (populations, areas, distances)
  - Historical facts and dates
  - Astronomical data (distances, times, celestial events)
  - Financial data (exchange rates, market info)
  - General knowledge (records, comparisons, statistics)
  - Date/time calculations and timezone conversions
- **lyrics** `[song]` - Retrieve song lyrics
- **whats_new** - Show recent bot updates and features

### 2. News & Current Events
- **news_top** `[category, country, limit]` - Get top news stories
  - Categories: general, business, tech, science, health, entertainment, sports, politics
  - Countries: in, us, ca, gb, au, etc. (default: in)
  - Limit: 1-3 articles (default: 3)
- **news_search** `[query, category, limit]` - Search for specific news
  - Search topics, people, events, companies
  - Filter by category and limit results
  - Covers both current and historical news

### 3. Entertainment & Games
- **gtn** - Start a number guessing game (1-10)
- **dice** `[sides]` - Roll dice (default: 6 sides)
- **flip** - Flip a coin (heads/tails)
- **ask** `[question]` - Get yes/no answers to questions

### 4. Media & Content
- **cat** - Share a random cat image
- **dog** - Share a random dog image  
- **gt** - Share a picture of GT
- **music** `[query]` - Play music in voice channel
- **leave** - Disconnect from voice channel

### 5. Server Management
- **purge** `[amount]` - Delete recent messages
- **clear** `[amount]` - Clear DM messages

## Response Guidelines

### Communication Style
- Keep responses concise but informative
- Use emojis thoughtfully to enhance communication (not excessively)
- Maintain a friendly, helpful tone
- Provide clear explanations for errors or issues
- Remember conversation context across interactions

### Tool Usage Rules
- Use **calculate** for ANY factual information, data queries, or knowledge questions
- Examples: population data, conversions, historical facts, scientific info, mathematical problems
- Use **news_top** for general news requests
- Use **news_search** for specific topics or targeted news queries
- For music playback, always verify the user is in a voice channel first
- Integrate tool results naturally into conversational responses

### Response Formatting
- Format responses for optimal Discord readability
- Include image URLs on separate lines for automatic display
- When receiving URLs from tools (especially calculate), display them directly
- Structure longer responses with clear sections
- Use code blocks for technical information when appropriate

### Error Handling
- Provide clear, user-friendly error messages
- Suggest alternatives when tools fail
- Maintain helpful tone even during errors
- Guide users toward successful interactions

## Message Processing
- Process messages in format "username: message"
- Respond only to the message content
- NEVER include usernames, prefixes, or labels in your responses
- Do NOT start responses with "Assistant:", "AI:", "Bot:", "LocalBot:" or any similar prefix
- Respond directly without any identification labels
- Maintain conversation context per server/DM
"""

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

ytdl_format_options = {
    "format": "bestaudio[ext=webm]/bestaudio/best",
    "outtmpl": os.path.join(music_dir, "%(title)s.%(ext)s"),
    "restrictfilenames": True,
    "noplaylist": False,
    "ignoreerrors": True,
    "prefer_ffmpeg": True,
    "quiet": True,
}

ffmpeg_options = {
    "before_options": "-nostdin",
    "options": "-vn -filter:a loudnorm",
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
                return_messages=True
            )

        memory = conversation_memory[context_key]

        if not gemini_client:
            await send_response(
                ctx,
                "Gemini client is not configured. Please check your GEMINI_API_KEY or GOOGLE_API_KEY.",
            )
            return None

        conversation_history = []
        chat_history = memory.chat_memory.messages

        for message in chat_history:
            if hasattr(message, "content"):
                if hasattr(message, "type") and message.type == "human":
                    conversation_history.append(f"User: {message.content}")
                elif hasattr(message, "type") and message.type == "ai":
                    conversation_history.append(f"Assistant: {message.content}")

        conversation_history.append(prompt)

        full_prompt = "Conversation:\n" + "\n".join(conversation_history)

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
            system_instruction=[
                types.Part.from_text(text=system_prompt),
            ],
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

        print(f"Executing tool: {tool_name} with arguments: {tool_arguments}")

        tool_actions = {
            "cat": lambda: cat(ctx, from_tool_call=send_directly),
            "dog": lambda: dog(ctx, from_tool_call=send_directly),
            "gtn": lambda: gtn(ctx, from_tool_call=send_directly),
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
            "news_top": lambda: news_top_stories(
                ctx,
                category=tool_arguments.get("category"),
                country=tool_arguments.get("country", "in"),
                limit=int(tool_arguments.get("limit", 3)),
                from_tool_call=send_directly,
            ),
            "news_search": lambda: news_search(
                ctx,
                query=tool_arguments.get("query"),
                category=tool_arguments.get("category"),
                limit=int(tool_arguments.get("limit", 3)),
                from_tool_call=send_directly,
            ),
            "gt": lambda: gt(ctx, from_tool_call=send_directly),
            "music": lambda: music_play(
                ctx, query=tool_arguments.get("query"), from_tool_call=send_directly
            ),
            "leave": lambda: music_leave(ctx, from_tool_call=send_directly),
            "whats_new": lambda: whats_new(ctx, from_tool_call=send_directly),
            "lyrics": lambda: lyrics(
                ctx, song_name=tool_arguments.get("song"), from_tool_call=send_directly
            ),
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
    "Latest news updates 📰",
    "Playing music 🎵",
    "Number guessing 🎲",
    "Rolling dice 🎯",
    "Flipping coins 🪙",
    "Managing messages 📝",
    "Fetching lyrics 🎤",
    "Breaking news alerts 📺",
    "Calculating math 🔢",
    "Sharing knowledge 📚",
    "Current events 🌍",
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
                    return_messages=True
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
                        # Check if this is the first tool call in the conversation
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

    # Check if file exists
    if not os.path.exists(filename):
        await ctx.followup.send(f"Error: Audio file not found: {filename}")
        return

    try:
        # Create audio source with error handling
        audio_source = discord.FFmpegPCMAudio(
            filename,
            before_options=ffmpeg_options["before_options"],
            options=ffmpeg_options["options"],
        )

        ctx.voice_client.play(
            audio_source,
            after=lambda e: bot.loop.create_task(after_playback(e, ctx)),
        )
        await ctx.followup.send(f'Now playing: {info["title"]}')
    except Exception as e:
        await ctx.followup.send(f"Error playing audio: {str(e)}")
        print(f"Audio playback error: {e}")


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
                # Get the actual downloaded filename
                filename = ydl.prepare_filename(entry)
                actual_file = find_downloaded_file(filename)

                if actual_file:
                    state["playlist_queue"].append(
                        {"info": entry, "filename": actual_file}
                    )
                else:
                    print(
                        f"Could not find downloaded file for: {entry.get('title', 'Unknown')}"
                    )

        elif info:
            # Get the actual downloaded filename
            filename = ydl.prepare_filename(info)
            actual_file = find_downloaded_file(filename)

            if actual_file:
                state["playlist_queue"].append({"info": info, "filename": actual_file})
            else:
                await ctx.followup.send(
                    f"Downloaded file not found. Check music directory."
                )
                return

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
async def lyrics(ctx, *, song_name: Optional[str] = None, from_tool_call: bool = False):
    state = await get_server_state(ctx.guild.id)
    if not from_tool_call:
        await ctx.response.defer()
    search_title = (
        song_name
        if song_name
        else state["current_song"]["title"] if state["current_song"] else None
    )

    if not search_title:
        message = "No song is currently playing and no song name was provided."
        if not from_tool_call:
            await ctx.followup.send(message)
        return message

    try:
        song = genius.search_song(search_title)
        if song:
            lyrics_text = song.lyrics
            if not from_tool_call:
                if len(lyrics_text) > 2000:
                    for i in range(0, len(lyrics_text), 2000):
                        await ctx.followup.send(lyrics_text[i : i + 2000])
                else:
                    await ctx.followup.send(lyrics_text)
            return lyrics_text[:500] + "..." if len(lyrics_text) > 500 else lyrics_text
        else:
            message = f"Lyrics for '{search_title}' not found."
            if not from_tool_call:
                await ctx.followup.send(message)
            return message
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if not from_tool_call:
            await ctx.followup.send(error_msg)
        return error_msg


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


async def news_top_stories(
    ctx,
    category: Optional[str] = None,
    country: str = "in",
    limit: int = 3,
    from_tool_call: bool = False,
) -> str:
    """Get top news stories using The News API."""
    try:
        if not NEWS_API_KEY:
            error_msg = "News API key not configured."
            if not from_tool_call:
                await send_response(ctx, error_msg)
            return error_msg

        # Build API URL
        base_url = "https://api.thenewsapi.com/v1/news/top"
        params = {
            "api_token": NEWS_API_KEY,
            "locale": country,
            "limit": min(limit, 3),  # Limit to max 3 articles
            "language": "en",
        }

        if category:
            params["categories"] = category

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"News API error {response.status}: {error_text[:200]}"
                    print(f"News API Error: {response.status} - {error_text}")
                    if not from_tool_call:
                        await send_response(ctx, "Sorry, I couldn't fetch the news.")
                    return error_msg

                data = await response.json()
                articles = data.get("data", [])

                if not articles:
                    message = "No news articles found."
                    if not from_tool_call:
                        await send_response(ctx, message)
                    return message

                # Format response
                news_emoji = "📰"
                category_text = f" in {category}" if category else ""
                response = f"{news_emoji} **Top Stories{category_text}:**\n\n"

                for i, article in enumerate(articles[:limit], 1):
                    title = article.get("title", "No title")
                    description = article.get("description", "")
                    source = article.get("source", "Unknown")
                    url = article.get("url", "")
                    published = article.get("published_at", "")

                    # Truncate description if too long
                    if description and len(description) > 100:
                        description = description[:100] + "..."

                    response += f"**{i}. {title}**\n"
                    if description:
                        response += f"{description}\n"
                    response += f"📅 {published[:10]} | 🔗 {source}\n"
                    if url:
                        response += f"{url}\n"
                    response += "\n"

                if not from_tool_call:
                    await send_response(ctx, response)
                return response

    except Exception as e:
        error_msg = f"Error fetching news: {str(e)}"
        print(f"News API Exception: {error_msg}")
        if not from_tool_call:
            await send_response(ctx, "Sorry, I couldn't fetch the news.")
        return error_msg


async def news_search(
    ctx,
    query: str,
    category: Optional[str] = None,
    limit: int = 3,
    from_tool_call: bool = False,
) -> str:
    """Search for specific news articles using The News API."""
    try:
        if not NEWS_API_KEY:
            error_msg = "News API key not configured."
            if not from_tool_call:
                await send_response(ctx, error_msg)
            return error_msg

        if not query:
            error_msg = "Search query is required."
            if not from_tool_call:
                await send_response(ctx, error_msg)
            return error_msg

        # Build API URL
        base_url = "https://api.thenewsapi.com/v1/news/all"
        params = {
            "api_token": NEWS_API_KEY,
            "search": query,
            "language": "en",
            "limit": min(limit, 3),  # Limit to max 3 articles
            "sort": "relevance_score",
        }

        if category:
            params["categories"] = category

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    error_msg = f"News API error: {response.status}"
                    if not from_tool_call:
                        await send_response(ctx, "Sorry, I couldn't search for news.")
                    return error_msg

                data = await response.json()
                articles = data.get("data", [])

                if not articles:
                    message = f"No news articles found for '{query}'."
                    if not from_tool_call:
                        await send_response(ctx, message)
                    return message

                # Format response
                search_emoji = "🔍"
                response = f"{search_emoji} **News Search Results for '{query}':**\n\n"

                for i, article in enumerate(articles[:limit], 1):
                    title = article.get("title", "No title")
                    description = article.get("description", "")
                    source = article.get("source", "Unknown")
                    url = article.get("url", "")
                    published = article.get("published_at", "")

                    # Truncate description if too long
                    if description and len(description) > 120:
                        description = description[:120] + "..."

                    response += f"**{i}. {title}**\n"
                    if description:
                        response += f"{description}\n"
                    response += f"📅 {published[:10]} | 📰 {source}\n"
                    if url:
                        response += f"🔗 {url}\n"
                    response += "\n"

                if not from_tool_call:
                    await send_response(ctx, response)
                return response

    except Exception as e:
        error_msg = f"Error searching news: {str(e)}"
        print(error_msg)
        if not from_tool_call:
            await send_response(ctx, "Sorry, I couldn't search for news.")
        return error_msg


@bot.slash_command(description="Get top news stories.")
async def getnews(ctx, category: Optional[str] = None, *, country: str = "in"):
    await news_top_stories(ctx, category=category, country=country)


@bot.slash_command(description="Search for news articles.")
async def searchnews(ctx, *, query: str):
    await news_search(ctx, query=query)


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


def find_downloaded_file(base_filename):
    """Find the actual downloaded file with various extensions."""
    possible_extensions = [".webm", ".mp3", ".m4a", ".mp4", ".opus"]
    base_name = os.path.splitext(base_filename)[0]

    for ext in possible_extensions:
        full_path = base_name + ext
        if os.path.exists(full_path):
            print(f"Found audio file: {full_path}")
            return full_path

    # Also check if the original filename exists
    if os.path.exists(base_filename):
        print(f"Found audio file: {base_filename}")
        return base_filename

    print(f"No audio file found for: {base_filename}")
    print(f"Checked: {[base_name + ext for ext in possible_extensions]}")
    return None


@bot.slash_command(description="List downloaded music files for debugging.")
async def list_music(ctx):
    """List all files in the music directory for debugging."""
    try:
        if not os.path.exists(music_dir):
            await ctx.respond("Music directory doesn't exist.")
            return

        files = os.listdir(music_dir)
        if not files:
            await ctx.respond("No files found in music directory.")
            return

        file_list = "\n".join(files[:10])  # Show first 10 files
        if len(files) > 10:
            file_list += f"\n... and {len(files) - 10} more files"

        await ctx.respond(
            f"**Music files ({len(files)} total):**\n```\n{file_list}\n```"
        )
    except Exception as e:
        await ctx.respond(f"Error listing music files: {str(e)}")


bot.run(TOKEN)
