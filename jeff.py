import discord, os, asyncio, requests
from discord.ext import commands
from dotenv import load_dotenv
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from typing import Optional

load_dotenv()
TOKEN = os.getenv("JEFF")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_history = {}


class MistralLLM(LLM):
    url = "http://localhost:11434/api/generate"

    @property
    def _llm_type(self) -> str:
        return "mistral-nemo"

    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        return asyncio.run(self._acall(prompt, stop=stop, **kwargs))

    async def _acall(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        headers = {"Content-Type": "application/json"}
        data = {"model": "mistral-nemo:latest", "prompt": prompt, "stream": False}
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.post(self.url, headers=headers, json=data)
        )
        return response.json()["response"]


template = """
You are chatting with Jeff, a friendly bot who loves to chat about anything and everything.
If anyone ask who are you, you can say:
"MY NAME IS JEFF"

Here is the conversation history:
{history}

Respond to the following prompt:
{Username}:{input}"""
prompt_template = PromptTemplate(
    input_variables=["history", "Username", "input"],
    template=template,
)
mistral_llm = MistralLLM()
llm_chain = LLMChain(llm=mistral_llm, prompt=prompt_template)


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


async def chat(ctx, *, message):
    channel_id = ctx.channel.id
    user_name = ctx.author.name
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    conversation_history[channel_id].append(f"{user_name}: {message}")
    history = "\n".join(conversation_history[channel_id])

    async with ctx.typing():
        try:
            response = await llm_chain.arun(
                history=history, Username=user_name, input=message
            )
            response = response.strip("Jeff:").strip()
            conversation_history[channel_id].append(f"Jeff: {response}")
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
            print(f"\n\nError: {e}\n\n")
            await ctx.reply("Sorry, I am unable to respond at the moment.")


bot.run(TOKEN)
