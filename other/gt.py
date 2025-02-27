import discord, os
from discord.ext import commands
from typing import Union
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
TOKEN = os.getenv("GT")


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_memory = {}
system_prompt = """Use as much profanity as possible."""
groq_api_key = os.environ.get("GT_KEY")
model_name = "mixtral-8x7b-32768"
groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)


async def generate_chat_completion(
    server_id: Union[str, None],
    channel_id: str,
    user_id: str,
    prompt: str,
) -> Union[str, None]:

    context_key = server_id if server_id is not None else f"DM-{channel_id}-{user_id}"

    global conversation_memory
    if "conversation_memory" not in globals():
        conversation_memory = {}
    if context_key not in conversation_memory:
        conversation_memory[context_key] = ConversationBufferWindowMemory(
            k=10, memory_key="chat_history", return_messages=True
        )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{human_input}"),
        ]
    )
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt_template,
        memory=conversation_memory[context_key],
        verbose=False,
    )
    response = conversation.predict(human_input=prompt)
    if "<tool_call>" in response and "</tool_call>" in response:
        response = "Failed to generate"
    return response


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
            server_id = str(ctx.guild.id) if ctx.guild else None
            channel_id = str(ctx.channel.id)
            user_id = str(ctx.author.id)
            username = ctx.author.display_name
            message = username + ": " + message

            response = await generate_chat_completion(
                prompt=message,
                server_id=server_id,
                channel_id=channel_id,
                user_id=user_id,
            )

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
            await ctx.reply(f"An error occurred: {e}")


@bot.command()
async def gtt(ctx):
    global conversation_memory
    conversation_memory = {}
    await ctx.send("Memory Cleared")


bot.run(TOKEN)
