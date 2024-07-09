# Local Bot

## Description
This Discord bot is a fun and interactive bot that provides various commands to users within a Discord server. It includes features such as ping testing, cat and dog images, dice rolling, number guessing game, coin flipping, chatting with the bot, and generating images based on prompts.

## Installation
1. Clone or download the repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Create a `.env` file in the root directory of the project.
4. Inside the `.env` file, add your Discord bot token in the following format:
    ```
    TOKEN=your_discord_bot_token_here
    ```
5. Ensure your bot has the necessary permissions in your Discord server.
6. Run the bot script by executing `python LocalBot.py` or `python LocalBot_phone.py` in your terminal, depending on your use case.

## Usage
Once the bot is running and connected to your Discord server, users can interact with it using various commands prefixed with `$`. The bot supports both traditional commands and slash commands for enhanced interaction within Discord.

### Available Commands

| Command                                    | Description                                                     | Options/Notes                                                                                                        |
| ------------------------------------------ | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `/cat` or `$cat`                           | Sends a random cat image.                                       |                                                                                                                      |
| `/dog` or `$dog`                           | Sends a random dog image.                                       |                                                                                                                      |
| `/gtn` or `$gtn`                           | Starts a number guessing game.                                  |                                                                                                                      |
| `/hello` or `$hello`                       | Greets the user.                                                |                                                                                                                      |
| `/dice [sides]` or `$dice [sides]`         | Rolls a dice with the specified number of sides.                | Default is 6 sides if none specified.                                                                                |
| `/flip` or `$flip`                         | Flips a coin.                                                   |                                                                                                                      |
| `/ask` or `$ask`                           | Provides a yes/no response randomly.                            |                                                                                                                      |
| `/chat [message]` or `$chat [message]`     | Engages in a chat with the bot using the text-generation model. |                                                                                                                      |
| `/imagine [prompt]` or `$imagine [prompt]` | Generates an image based on the provided prompt.                | `--magic`: Uses a magic prompt.<br>`--model`: Specify the model to use for image generation. Range: [0, 1, 2, 3, 4]. |
| `/purge [amount]` or `$purge [amount]`     | Deletes the specified number of messages in the channel.        | Requires the `Manage Messages` permission.                                                                           |
| `$clear [amount]`     | Clears the specified number of messages in the DM.              |                                                                                                                      |

## Contributing
Contributions to the project are welcome. If you have any suggestions, bug fixes, or additional features you'd like to implement, feel free to fork the repository, make your changes, and submit a pull request.

## Dependencies
- discord.py: For creating and managing the Discord bot.
- python-dotenv: For managing environment variables.
- requests: For making HTTP requests (used in some commands for fetching data).
- py-cord: For supporting slash commands.
- transformers: For text-generation capabilities in chat interactions.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.