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
            
            
            
