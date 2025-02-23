# LocalBot

A versatile Discord bot powered by AI, capable of natural conversations, image generation, music playback, and various utility functions.

## 🌟 Features

### 🤖 AI Integration
- Natural conversation with context memory
- AI-powered image generation using Stable Diffusion
- Smart responses with emoji support

### 🎵 Media & Entertainment
- YouTube music playback with playlist support
- Song lyrics fetching
- Random cat and dog images
- Custom image responses

### 🔧 Utility Functions
- Weather updates with detailed information
- Mathematical calculations and queries
- Message management and moderation tools
- Conversation history management

### 🎮 Games & Fun
- Number guessing game
- Dice rolling with custom sides
- Coin flipping
- Magic 8-ball style questions

## 📋 Requirements

- Python 3.8+
- Discord.py
- Additional dependencies listed in `requirements.txt`

## ⚙️ Setup

1. **Clone and Setup**
```sh
git clone https://github.com/ifsvivek/LocalBot.git
cd LocalBot
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

2. **Environment Configuration**
Create a `.env` file with your API keys:
```env
TOKEN=your_discord_bot_token
GENIUS_TOKEN=your_genius_api_token
WOLF=your_wolframalpha_api_key
GROQ_API_KEY=your_groq_api_key
WEATHER_API_KEY=your_openweathermap_api_key
```

## 🎮 Commands

### 💬 Chat & AI
- `@LocalBot [message]` - Chat with the bot
- `/imagine [prompt]` - Generate AI images
- `/calculate [query]` - Solve mathematical queries
- `/weather [city]` - Get weather information

### 🎵 Music
- `/play [query]` - Play music from YouTube
- `/stop` - Stop current playback
- `/lyrics [song]` - Get song lyrics
- `/join` - Join voice channel
- `/leave` - Leave voice channel

### 🎲 Games
- `/gtn` - Guess the number
- `/dice [sides]` - Roll dice
- `/flip` - Flip a coin
- `/ask [question]` - Ask yes/no questions

### 📷 Images
- `/cat` - Random cat image
- `/dog` - Random dog image
- `/gt` - GT meme image

### ⚡ Utility
- `/purge [amount]` - Delete messages
- `$clear [amount]` - Clear DM messages
- `$clear_history` - Reset chat memory
- `$pin` - Pin replied message

## 🛠️ Development

- Built with Python and Discord.py
- Uses Groq for AI processing
- Integrated with Stable Diffusion for image generation
- Supports multiple API integrations

## 📜 License

This project is licensed under the MIT License - see the [`LICENSE`](./LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.