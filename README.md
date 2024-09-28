# LocalBot

LocalBot is a versatile Discord bot designed to chat with users, generate images based on prompts, play songs from YouTube, and fetch song lyrics. It also includes various fun commands like rolling dice, flipping coins, and more.

## Features

- **Chat with Users**: Engage in conversations with users.
- **Image Generation**: Generate images based on user prompts.
- **Music Playback**: Play songs from YouTube and fetch lyrics.
- **Fun Commands**: Includes commands like rolling dice, flipping coins, and guessing games.
- **Moderation Tools**: Commands to delete messages and manage conversations.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ifsvivek/LocalBot.git
    cd LocalBot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your tokens:
    ```env
    TOKEN=your_discord_bot_token
    GENIUS_TOKEN=your_genius_api_token
    WOLF=your_wolframalpha_api_key
    GROQ_API_KEY=your_groq_api_key
    ```

## Usage

Run the bot:
```sh
python LocalBot.py
```

## Commands

### Chat Commands

- **Chat with the bot**: `$chat [message]`
- **Generate an image**: `/imagine [prompt]`
- **Get song lyrics**: `/lyrics [song_name]`

### Fun Commands

- **Send a picture of a cat**: `/cat`
- **Send a picture of a dog**: `/dog`
- **Guess the number game**: `/gtn`
- **Say hello**: `/hello`
- **Roll a dice**: `/dice [sides]`
- **Flip a coin**: `/flip`
- **Ask a yes/no question**: `/ask [question]`

### Music Commands

- **Play a song from YouTube**: `/play [query]`
- **Stop the current playback**: `/stop`
- **Join a voice channel**: `/join`
- **Leave a voice channel**: `/leave`

### Moderation Commands

- **Delete messages**: `/purge [amount]`
- **Clear bot messages in DM**: `$clear [amount]`
- **Clear conversation history**: `$clear_history`
- **Pin a replied message**: `$pin`

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [`LICENSE`](./LICENSE) file for details.


---