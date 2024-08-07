## Description
This Discord bot is a fun and interactive bot that provides various commands to users within a Discord server. It includes features such as ping testing, cat and dog images, dice rolling, number guessing game, coin flipping, chatting with the bot, and generating images based on prompts.

## Installation
1. Clone or download the repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Create a `.env` file in the root directory of the project.
4. Inside the `.env` file, add your Discord bot token in the following format:
    ```
    TOKEN=your_discord_bot_token_here
    GENIUS_TOKEN=your_genius_token_here
    API_KEY=your_openwebui_token_here
    SERVER_URL=your_openwebui_server_url_here
    MODEL=model_name_here
    ```
5. Ensure your bot has the necessary permissions in your Discord server.
6. Run the bot script by executing `python LocalBot.py` or `python LocalBot_phone.py` in your terminal, depending on your use case.
7. or use `nohup python3 LocalBot.py &` to run the bot in the background.

## Usage
Once the bot is running and connected to your Discord server, users can interact with it using various commands prefixed with `$`. The bot supports both traditional commands and slash commands for enhanced interaction within Discord.

### Available Commands

| Command                                | Description                                                     | Options/Notes                                                                                                          |
| -------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `/cat` or `$cat`                       | Sends a random cat image.                                       |                                                                                                                        |
| `/dog` or `$dog`                       | Sends a random dog image.                                       |                                                                                                                        |
| `/gtn` or `$gtn`                       | Starts a number guessing game.                                  |                                                                                                                        |
| `/hello` or `$hello`                   | Greets the user.                                                |                                                                                                                        |
| `/dice [sides]` or `$dice [sides]`     | Rolls a dice with the specified number of sides.                | Default is 6 sides if none specified.                                                                                  |
| `/flip` or `$flip`                     | Flips a coin.                                                   |                                                                                                                        |
| `/ask` or `$ask`                       | Provides a yes/no response randomly.                            |                                                                                                                        |
| `/chat [message]` or `$chat [message]` | Engages in a chat with the bot using the text-generation model. |                                                                                                                        |
| `$imagine [prompt]`                    | Generates an image based on the provided prompt.                | `--magic`: Uses a magic prompt.<br>`--model`: Specify the model to use for image generation. Range: [0, 1, 2, 3, 4,5]. |
| `/purge [amount]` or `$purge [amount]` | Deletes the specified number of messages in the channel.        | Requires the `Manage Messages` permission.                                                                             |
| `$clear [amount]`                      | Clears the specified number of messages in the DM.              |                                                                                                                        |
| `/join` or                             | Joins the voice channel of the user.                            |                                                                                                                        |
| `/leave` or                            | Leaves the voice channel.                                       |                                                                                                                        |
| `/play [song]` or                      | Plays the specified song in the voice channel.                  |                                                                                                                        |
| `/stop` or                             | Stops the currently playing song.                               |                                                                                                                        |
| `/lyrics `                             | Fetches the lyrics of the specified song.                       |                                                                                                                        |

## Contributing
Contributions to the project are welcome. If you have any suggestions, bug fixes, or additional features you'd like to implement, feel free to fork the repository, make your changes, and submit a pull request.

## Dependencies
- discord.py: For creating and managing the Discord bot.
- python-dotenv: For managing environment variables.
- requests: For making HTTP requests (used in some commands for fetching data).
- py-cord: For supporting slash commands.
- transformers: For text-generation capabilities in chat interactions.
- lyricsgenius : For fetching song lyrics.
- youtube_dl: For playing music in voice channels.
- ffmpeg: For audio processing in voice channels.
- Pillow: For image processing and generation.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.