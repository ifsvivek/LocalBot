import discord, requests, json, random, asyncio, os, base64, argparse, time
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor


load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
model_name = "llama3"


def ollama_chat(prompt, model):
    payload = {"prompt": prompt, "model": model, "max_tokens": 150}
    response = requests.post(OLLAMA_API_URL, json=payload)
    response.raise_for_status()
    parts = response.text.strip().split("\n")
    combined_response = ""
    for part in parts:
        json_part = json.loads(part)
        combined_response += json_part.get("response", "")
    return combined_response


def generate_image(
    prompt, model_id=0, use_refiner=False, magic_prompt=False, calc_metrics=False
):
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

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        base64_image_string = data["image"]
        image_data = base64.b64decode(base64_image_string)
        image = Image.open(BytesIO(image_data))
        timestamp = int(time.time())
        image_path = os.path.join(output_dir, f"img_{timestamp}.png")
        image.save(image_path)

        return image_path
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
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        cat_image_link = data[0]["url"]
        await ctx.respond(cat_image_link)
    else:
        await ctx.respond("Failed to fetch cat image. Try again later.")


@bot.slash_command(description="Send a picture of a dog.")
async def dog(ctx):
    response = requests.get("https://api.thedogapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        dog_image_link = data[0]["url"]
        await ctx.respond(dog_image_link)
    else:
        await ctx.respond("Failed to fetch dog image. Try again later.")


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
            if ctx.message.reference:
                original_message = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                message = original_message.content + "\n" + message

            response = ollama_chat(message, model_name)
            is_first_chunk = True
            while response:
                split_at = response.rfind("\n", 0, 2000)
                if split_at == -1 or split_at > 2000:
                    split_at = 2000
                chunk = response[:split_at].strip()
                response = response[split_at:].strip()

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
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            image_path = await loop.run_in_executor(
                pool,
                lambda: generate_image(
                    prompt=prompt,
                    model_id=parsed_args.model,
                    use_refiner=parsed_args.refiner,
                    magic_prompt=parsed_args.magic,
                ),
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

    await ctx.message.reply(embed=embed)


bot.run(TOKEN)
