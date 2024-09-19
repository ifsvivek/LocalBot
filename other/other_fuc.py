async def generate_text(
    server_id: Union[str, None],
    channel_id: str,
    user_id: str,
    prompt: str,
    user_name: str,
) -> Union[str, None]:
    global conversation_history

    # Handle conversation history differently for server and DM contexts
    if server_id is not None:
        if server_id not in conversation_history:
            conversation_history[server_id] = {}
        if channel_id not in conversation_history[server_id]:
            conversation_history[server_id][channel_id] = {}
        if user_id not in conversation_history[server_id][channel_id]:
            conversation_history[server_id][channel_id][user_id] = []
        conversation_history[server_id][channel_id][user_id].append(
            f"{user_name}: {prompt}"
        )
    else:
        # Use "DM" as a key for direct messages to differentiate from server contexts
        dm_key = "DM"
        if dm_key not in conversation_history:
            conversation_history[dm_key] = {}
        if channel_id not in conversation_history[dm_key]:
            conversation_history[dm_key][channel_id] = {}
        if user_id not in conversation_history[dm_key][channel_id]:
            conversation_history[dm_key][channel_id][user_id] = []
        conversation_history[dm_key][channel_id][user_id].append(
            f"{user_name}: {prompt}"
        )

    # Append the system prompt if not already present
    if system_prompt:
        system_message = f"System: {system_prompt}"
        if server_id is not None:
            if (
                system_message
                not in conversation_history[server_id][channel_id][user_id]
            ):
                conversation_history[server_id][channel_id][user_id].insert(
                    0, system_message
                )
        else:
            if system_message not in conversation_history[dm_key][channel_id][user_id]:
                conversation_history[dm_key][channel_id][user_id].insert(
                    0, system_message
                )

    # Construct the context
    if server_id is not None:
        context = "\n".join(conversation_history[server_id][channel_id][user_id])
    else:
        context = "\n".join(conversation_history[dm_key][channel_id][user_id])

    # Prepare the request
    url = f"{SERVER_URL}/ollama/api/generate"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "prompt": f"<context>{context}</context>\n\nBot:",
        "stream": False,
    }

    # Send the request and handle the response
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                bot_response = result.get("response", "")
                if server_id is not None:
                    conversation_history[server_id][channel_id][user_id].append(
                        f"Bot: {bot_response}"
                    )
                else:
                    conversation_history[dm_key][channel_id][user_id].append(
                        f"Bot: {bot_response}"
                    )
                return bot_response
            else:
                return f"Error: Request failed with status code {response.status}"
            
            
            
@bot.slash_command(description="Generate an image based on a prompt.")
async def flux(ctx, *, prompt):
    async def send_initial_message():
        if hasattr(ctx, "respond"):
            return await ctx.respond("Generating image, please wait...")
        else:
            return await ctx.reply("Generating image, please wait...")

    async def edit_message(initial_message, content=None, embed=None, file=None):
        await initial_message.edit(content=content, embed=embed, file=file)

    try:
        initial_message = await send_initial_message()

        start_time = time.time()
        result = subprocess.run(
            [".venv/bin/python", "genflux.py", prompt], capture_output=True, text=True
        )
        end_time = time.time()
        time_taken = end_time - start_time

        if result.returncode == 0:
            image_path = "img/flux-dev.png"
            embed_title = prompt[:253] + "..." if len(prompt) > 256 else prompt
            embed = discord.Embed(title=embed_title, color=0x00FF00)
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
        print(f"An error occurred: {e}")
        if hasattr(ctx, "respond"):
            await ctx.respond("An error occurred while generating the image.")
        else:
            await ctx.reply("An error occurred while generating the image.")