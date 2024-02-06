# Local Bot

## Description
This Discord bot is a fun and interactive bot that provides various commands to users within a Discord server. It includes features such as ping testing, cat images, dice rolling, number guessing game, coin flipping, and more.

## Installation
1. Clone or download the repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Create a `.env` file in the root directory of the project.
4. Inside the `.env` file, add your Discord bot token in the following format:
    ```
    TOKEN=your_discord_bot_token_here
    ```
5. Ensure your bot has the necessary permissions in your Discord server.
6. Run the bot script by executing `python bot.py` in your terminal.

## Usage
Once the bot is running and connected to your Discord server, users can interact with it using various commands prefixed with `$`.

### Available Commands
- `$ping [target]`: Tests the latency to a specified target (default is `1.1.1.1`).
- `$cat`: Sends a random cat image.
- `$echo [message]`: Repeats the provided message.
- `$gtn`: Starts a number guessing game.
- `$hello`: Greets the user.
- `$dice [sides]`: Rolls a dice with the specified number of sides (default is 6).
- `$flip`: Flips a coin.
- `$shalli`: Provides a yes/no response randomly.

## Contributing
Contributions to the project are welcome. If you have any suggestions, bug fixes, or additional features you'd like to implement, feel free to fork the repository, make your changes, and submit a pull request.