import discord, requests, json, random, asyncio, os, shlex, base64, argparse, time
from dotenv import load_dotenv
from discord.ext import commands
from discord import File
from PIL import Image
from io import BytesIO


load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
model_name = "tinyllama"
chunk_size = 2000


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


def generate_image(prompt, model_id=0, use_refiner=False, magic_prompt=False):
    output_dir = "img"
    os.makedirs(output_dir, exist_ok=True)

    url = "https://diffusion.ayushmanmuduli.com/gen"
    params = {
        "prompt": prompt,
        "model_id": model_id,
        "use_refiner": use_refiner,
        "magic_prompt": magic_prompt,
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
    await bot.change_presence(activity=discord.Game(name="Running on phone"))


@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        ctx = await bot.get_context(message)
        await chat(
            ctx, message=message.content.replace(f"<@{bot.user.id}>", "").strip()
        )
    else:
        await bot.process_commands(message)


@bot.command(description="Send a picture of a cat.")
async def cat(ctx):
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    if response.status_code == 200:
        data = response.json()
        cat_image_link = data[0]["url"]
        await ctx.message.reply(cat_image_link)
    else:
        await ctx.message.reply("Failed to fetch cat image. Try again later.")


@bot.command(description="Send a picture of a dog.")
async def dog(ctx):
    try:
        response = requests.get("https://api.thedogapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            dog_image_link = data[0]["url"]
            await ctx.message.reply(dog_image_link)
        else:
            await ctx.message.reply("Failed to fetch dog image. Try again later.")
    except Exception as e:
        await ctx.message.reply(f"An error occurred: {e}")


@bot.command(description="Game: Guess the number between 1 and 10.")
async def gtn(ctx):
    secret_number = random.randint(1, 10)
    print("Secret Number:", secret_number)
    await ctx.message.reply("Guess a number between 1 and 10.")

    def check(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        guess = await bot.wait_for("message", check=check, timeout=10.0)
        guess_number = int(guess.content)
        if 1 <= guess_number <= 10:
            if guess_number == secret_number:
                await ctx.message.reply("You guessed it!")
            else:
                await ctx.message.reply("Nope, try again.")
        else:
            await ctx.message.reply("Please enter a number between 1 and 10.")
    except asyncio.TimeoutError:
        await ctx.message.reply("Time is up! You took too long to guess.")


@bot.command(description="Tell the user hello.")
async def hello(ctx):
    await ctx.message.reply(f"Hello, {ctx.author.name}!")


@bot.command(description="Roll a dice with the specified number of sides.")
async def dice(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.message.reply(f"You rolled a {result}.")


@bot.command(description="Flip a coin.")
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.message.reply(f"The coin landed on: **{result}**")


@bot.command(description="Ask the bot a yes/no question.")
async def ask(ctx):
    result = random.choice(["Yes", "No"])
    await ctx.message.reply(result)


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
    args_list = shlex.split(args)
    prompt_parts = []
    while args_list and not args_list[0].startswith("--"):
        prompt_parts.append(args_list.pop(0))
    prompt = " ".join(prompt_parts)
    parser = argparse.ArgumentParser(
        description="Generate an image based on a prompt.", add_help=False
    )
    parser.add_argument("--model", type=int, default=0, help="The model ID to use.")
    parser.add_argument(
        "--refiner", action="store_true", help="Whether to use the refiner."
    )
    parser.add_argument(
        "--magic", action="store_true", help="Whether to use magic prompt."
    )

    try:
        parsed_args, unknown = parser.parse_known_args(args_list)
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
        with open(image_path, "rb") as image:
            await ctx.message.reply(file=File(image, filename="image.png"))
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print(e)


bot.run(TOKEN)
