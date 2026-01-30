import os, random, asyncio, aiohttp, json, discord
from discord.ext import commands, tasks
from typing import Optional
from langchain_classic.memory import ConversationBufferWindowMemory
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
WOLF = os.getenv("WOLF")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

conversation_memory = {}
system_prompt = """
# LocalBot System Instructions

## Identity
You are LocalBot, a helpful Discord bot designed to provide a natural and engaging experience. Your personality is friendly, helpful, and conversational while remaining professional.

## Core Capabilities
- Natural conversation with thoughtful emoji usage
- Real-time weather information
- Interactive games and utilities
- Mathematical calculations and data queries
- Media sharing and management

## Available Tools
The following tools are available to you. You should use them whenever necessary to provide accurate and helpful information.

1. **weather** - Get current weather statistics for any city.
2. **calculate** - Use Wolfram Alpha for any factual information, math, conversions, or data queries.
3. **lyrics** - Retrieve song lyrics.
4. **whats_new** - Show recent bot updates and features.
5. **gtn** - Start a number guessing game.
6. **dice** - Roll dice.
7. **flip** - Flip a coin.
8. **ask** - Get yes/no answers to questions.
9. **meme** - Get a random meme.
10. **crypto** - Get cryptocurrency prices.
11. **cat/dog/gt** - Get random animal or GT pictures.
12. **serverinfo/userinfo** - Get server or user information.
13. **purge/clear** - Manage server or DM messages.

## Response Guidelines

### Communication Style
- Keep responses concise but informative
- Use emojis thoughtfully to enhance communication (not excessively)
- Maintain a friendly, helpful tone
- Provide clear explanations for errors or issues
- Remember conversation context across interactions

### Response Formatting
- Format responses for optimal Discord readability
- Include image URLs on separate lines for automatic display
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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform mathematical calculations or factual queries using Wolfram Alpha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The math query or factual question.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get current weather statistics for a specific city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of the city."}
                },
                "required": ["city"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cat",
            "description": "Get a random picture of a cat.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dog",
            "description": "Get a random picture of a dog.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meme",
            "description": "Get a random meme from Reddit.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gtn",
            "description": "Start a number guessing game (1-10).",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dice",
            "description": "Roll a dice with a specified number of sides.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sides": {
                        "type": "integer",
                        "description": "Number of sides (default 6).",
                    }
                },
                "required": ["sides"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flip",
            "description": "Flip a coin.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask",
            "description": "Ask a yes/no question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask.",
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crypto",
            "description": "Get the current price for a cryptocurrency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The crypto symbol (e.g. BTC, ETH).",
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "purge",
            "description": "Delete a specified number of messages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "Number of messages to delete.",
                    }
                },
                "required": ["amount"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "serverinfo",
            "description": "Get information about the current server.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "userinfo",
            "description": "Get information about a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "The user mention or ID (optional).",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "whats_new",
            "description": "Show recent bot updates.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "gt",
            "description": "Share a picture of GT.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]

cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY) if CEREBRAS_API_KEY else None


async def send_response(ctx, message):
    if hasattr(ctx, "respond"):
        await ctx.respond(message)
    else:
        await ctx.reply(message)
    return message


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
    """Generate a chat completion response using Cerebras with native tool calling."""
    try:
        global conversation_memory
        context_key = server_id if server_id else f"DM-{channel_id}-{user_id}"

        if context_key not in conversation_memory:
            conversation_memory[context_key] = ConversationBufferWindowMemory(
                return_messages=True
            )

        memory = conversation_memory[context_key]

        if not cerebras_client:
            await send_response(
                ctx,
                "Cerebras client is not configured. Please check your CEREBRAS_API_KEY.",
            )
            return None

        # Build consistent messages format for Cerebras
        messages = [{"role": "system", "content": system_prompt}]
        chat_history = memory.chat_memory.messages
        for msg in chat_history:
            if hasattr(msg, "content"):
                role = "user" if msg.type == "human" else "assistant"
                messages.append({"role": role, "content": msg.content})

        # Add the current prompt
        messages.append({"role": "user", "content": prompt})

        models_to_try = ["gpt-oss-120b", "llama-3.3-70b"]
        response_text = None
        last_error = None

        for model_name in models_to_try:
            try:
                # Local copy of messages for the loop
                curr_messages = list(messages)
                tool_use_depth = 0
                max_depth = 5

                while tool_use_depth < max_depth:
                    response = cerebras_client.chat.completions.create(
                        messages=curr_messages,
                        model=model_name,
                        tools=TOOLS,
                        max_completion_tokens=1024,
                        temperature=0.7,
                    )

                    assistant_message = response.choices[0].message
                    curr_messages.append(assistant_message)

                    if assistant_message.tool_calls:
                        tool_use_depth += 1
                        for tool_call in assistant_message.tool_calls:
                            result = await handle_tool_call(
                                ctx, tool_call, send_directly=True
                            )
                            curr_messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": json.dumps({"result": result}),
                                }
                            )
                        continue  # Call model again with tool results
                    else:
                        response_text = assistant_message.content
                        break

                if response_text:
                    break
            except Exception as e:
                print(f"Error with model {model_name}: {e}")
                last_error = e
                continue

        if not response_text:
            raise last_error or Exception("Failed to get response from Cerebras models")

        memory.chat_memory.add_user_message(prompt)
        memory.chat_memory.add_ai_message(response_text)

        return response_text

    except Exception as e:
        print(f"Cerebras completion error: {e}")
        await send_response(ctx, "I encountered an error processing your request.")
        return None


async def handle_tool_call(
    ctx: commands.Context,
    tool_call,
    send_directly: bool = False,
) -> str:
    """Handle native tool calls from Cerebras."""
    try:
        tool_name = tool_call.function.name
        tool_arguments = json.loads(tool_call.function.arguments)

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
            "gt": lambda: gt(ctx, from_tool_call=send_directly),
            "whats_new": lambda: whats_new(ctx, from_tool_call=send_directly),
            "meme": lambda: meme(ctx, from_tool_call=send_directly),
            "crypto": lambda: crypto_price(
                ctx,
                symbol=tool_arguments.get("symbol"),
                from_tool_call=send_directly,
            ),
            "serverinfo": lambda: server_info(ctx, from_tool_call=send_directly),
            "userinfo": lambda: user_info(
                ctx,
                user=tool_arguments.get("user"),
                from_tool_call=send_directly,
            ),
        }

        if tool_name not in tool_actions:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = await tool_actions[tool_name]()
        return result

    except Exception as e:
        print(f"Tool execution error: {e}")
        return f"Error: {str(e)}"


statuses = [
    "Ask me anything! 💭",
    "Weather forecasts 🌤️",
    "Powered by Cerebras AI 🧠",
    "Number guessing 🎲",
    "Rolling dice 🎯",
    "Flipping coins 🪙",
    "Managing messages 📝",
    "Calculating math 🔢",
    "Sharing knowledge 📚",
    "Current events 🌍",
    "Running on local power 🔋",
    "Processing requests ⚡",
    "Native tool calling 🛠️",
    "Learning new tricks 🎓",
    "Here to help! 👋",
    "Chat with me 💬",
    "Ready for commands ⌨️",
    "Local assistant 🤝",
    "Online and active ✨",
    "Fast responses ⚡",
    "24/7 Service 🕒",
    "Version 5.0 🆕",
    "Crypto prices 💰",
    "Random memes 😂",
    "Cat & dog pics 🐱🐶",
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

            full_prompt = f"{username}: {message}"

            response = await generate_chat_completion(
                ctx=ctx,
                prompt=full_prompt,
                server_id=server_id,
                channel_id=channel_id,
                user_id=user_id,
            )

            if response:
                await send_complete_response(ctx, response)
            else:
                await ctx.reply(
                    "I couldn't generate a response. Please try again later."
                )

        except Exception as e:
            print(f"Chat error: {e}")
            await ctx.reply(f"An error occurred: {e}")


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


async def meme(ctx, from_tool_call=False):
    """Get a random meme from Reddit."""
    try:
        subreddits = [
            "memes",
            "dankmemes",
            "me_irl",
            "wholesomememes",
            "funny",
            "ProgrammerHumor",
            "PrequelMemes",
            "terriblefacebookmemes",
        ]
        subreddit = random.choice(subreddits)

        async with aiohttp.ClientSession() as session:
            # Try to get a meme from the subreddit's hot posts
            async with session.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50",
                headers={"User-Agent": "LocalBot/1.0"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get("data", {}).get("children", [])

                    # Filter for image posts
                    image_posts = [
                        post
                        for post in posts
                        if post["data"]
                        .get("url", "")
                        .endswith((".jpg", ".png", ".gif", ".jpeg"))
                        and not post["data"].get("over_18", False)
                    ]

                    if image_posts:
                        post_data = random.choice(image_posts)["data"]
                        title = post_data.get("title", "No title")
                        url = post_data.get("url", "")
                        ups = post_data.get("ups", 0)

                        message = f"**{title}** 👍 {ups}\n{url}"
                        if not from_tool_call:
                            await send_response(ctx, message)
                        return message

        # Fallback
        message = "Couldn't fetch a meme right now. Try again! 😅"
        if not from_tool_call:
            await send_response(ctx, message)
        return message
    except Exception as e:
        error_msg = f"Error fetching meme: {str(e)}"
        print(f"Meme fetch error: {error_msg}")
        if not from_tool_call:
            await send_response(ctx, "Failed to fetch a meme. Try again!")
        return error_msg


@bot.slash_command(description="Get a random meme.")
async def getmeme(ctx):
    await meme(ctx)


async def crypto_price(ctx, symbol: str, from_tool_call=False):
    """Get cryptocurrency price."""
    try:
        symbol_upper = symbol.upper()

        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "USDC": "usd-coin",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "ADA": "cardano",
            "TRX": "tron",
            "AVAX": "avalanche-2",
            "SHIB": "shiba-inu",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LTC": "litecoin",
            "DAI": "dai",
            "LINK": "chainlink",
            "UNI": "uniswap",
        }

        coin_id = symbol_map.get(symbol_upper, symbol.lower())

        async with aiohttp.ClientSession() as session:
            # Try CoinGecko API (more reliable)
            async with session.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        price = coin_data.get("usd", 0)
                        change_24h = coin_data.get("usd_24h_change", 0)
                        market_cap = coin_data.get("usd_market_cap", 0)

                        # Format numbers
                        if price >= 1000:
                            price_str = f"${price:,.0f}"
                        elif price >= 1:
                            price_str = f"${price:,.2f}"
                        else:
                            price_str = f"${price:.6f}"

                        if market_cap > 1e9:
                            market_cap_str = f"${market_cap/1e9:.2f}B"
                        elif market_cap > 1e6:
                            market_cap_str = f"${market_cap/1e6:.2f}M"
                        else:
                            market_cap_str = f"${market_cap:,.0f}"

                        change_emoji = "📈" if change_24h > 0 else "📉"
                        change_sign = "+" if change_24h > 0 else ""

                        message = (
                            f"💰 **{symbol_upper}**\n"
                            f"💵 Price: {price_str}\n"
                            f"{change_emoji} 24h Change: {change_sign}{change_24h:.2f}%\n"
                            f"📊 Market Cap: {market_cap_str}"
                        )

                        if not from_tool_call:
                            await send_response(ctx, message)
                        return message

        message = f"Couldn't find price for {symbol_upper}. Try BTC, ETH, SOL, or other popular cryptocurrencies."
        if not from_tool_call:
            await send_response(ctx, message)
        return message
    except Exception as e:
        error_msg = f"Error fetching crypto price: {str(e)}"
        if not from_tool_call:
            await send_response(ctx, f"Failed to get price for {symbol}.")
        return error_msg


@bot.slash_command(description="Get cryptocurrency price.")
async def crypto(ctx, *, symbol: str):
    await crypto_price(ctx, symbol)


async def server_info(ctx, from_tool_call=False):
    """Display server information."""
    try:
        if not ctx.guild:
            message = "This command only works in servers, not DMs."
            if not from_tool_call:
                await send_response(ctx, message)
            return message

        guild = ctx.guild

        # Get various counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles)
        emojis = len(guild.emojis)

        # Get member stats
        total_members = guild.member_count

        # Get boost info
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count

        # Creation date
        created_at = guild.created_at.strftime("%B %d, %Y")

        message = (
            f"🏰 **{guild.name}**\n\n"
            f"👑 Owner: {guild.owner.mention if guild.owner else 'Unknown'}\n"
            f"👥 Members: {total_members}\n"
            f"📅 Created: {created_at}\n\n"
            f"📊 **Channels:**\n"
            f"💬 Text: {text_channels}\n"
            f"🔊 Voice: {voice_channels}\n"
            f"📁 Categories: {categories}\n\n"
            f"🎭 Roles: {roles}\n"
            f"😀 Emojis: {emojis}\n"
            f"⚡ Boost Level: {boost_level} ({boost_count} boosts)"
        )

        if not from_tool_call:
            await send_response(ctx, message)
        return message
    except Exception as e:
        error_msg = f"Error getting server info: {str(e)}"
        if not from_tool_call:
            await send_response(ctx, "Failed to get server information.")
        return error_msg


@bot.slash_command(description="Display server information.")
async def serverinfo(ctx):
    await server_info(ctx)


async def user_info(ctx, user: Optional[str] = None, from_tool_call=False):
    """Display user information."""
    try:
        # Get the user to display info about
        target_user = ctx.author
        if user and ctx.guild:
            # Try to get mentioned user
            if ctx.message and ctx.message.mentions:
                target_user = ctx.message.mentions[0]

        # Get user details
        username = target_user.name
        discriminator = (
            target_user.discriminator if hasattr(target_user, "discriminator") else ""
        )
        user_id = target_user.id
        created_at = target_user.created_at.strftime("%B %d, %Y")
        avatar_url = target_user.display_avatar.url

        message = (
            f"👤 **User Information**\n\n"
            f"Name: {username}#{discriminator if discriminator != '0' else ''}\n"
            f"ID: {user_id}\n"
            f"Created: {created_at}\n"
            f"Avatar: {avatar_url}"
        )

        # Add server-specific info if in a guild
        if ctx.guild and isinstance(target_user, discord.Member):
            joined_at = (
                target_user.joined_at.strftime("%B %d, %Y")
                if target_user.joined_at
                else "Unknown"
            )
            top_role = target_user.top_role.name if target_user.top_role else "None"

            message += (
                f"\n\n**Server Info:**\n"
                f"Joined: {joined_at}\n"
                f"Nickname: {target_user.nick or 'None'}\n"
                f"Top Role: {top_role}"
            )

        if not from_tool_call:
            await send_response(ctx, message)
        return message
    except Exception as e:
        error_msg = f"Error getting user info: {str(e)}"
        if not from_tool_call:
            await send_response(ctx, "Failed to get user information.")
        return error_msg


@bot.slash_command(description="Display user information.")
async def userinfo(ctx, user: Optional[discord.Member] = None):
    await user_info(ctx, str(user.id) if user else None)


bot.run(TOKEN)
