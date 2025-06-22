<div align="center">

# 🤖 LocalBot

_A powerful Discord bot powered by Google's Gemini AI_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-4285f4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

_Natural conversations • Music playback • Games & Entertainment • Utility functions_

[Features](#-features) • [Setup](#️-setup) • [Commands](#-commands) • [Contributing](#-contributing)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### � **AI Integration**

-   🗣️ Natural conversation with context memory
-   🤖 Powered by **Google Gemini 2.5 Flash**
-   💭 Smart responses with emoji support
-   🧠 Advanced conversational AI capabilities

### 🎵 **Media & Entertainment**

-   🎶 YouTube music playback with playlist support
-   🎤 Song lyrics fetching via Genius API
-   🐱 Random cat and dog images
-   🖼️ Custom image responses

</td>
<td width="50%">

### 🔧 **Utility Functions**

-   🌤️ Weather updates with detailed information
-   🧮 Mathematical calculations via Wolfram Alpha
-   🛠️ Message management and moderation tools
-   💾 Conversation history management

### 🎮 **Games & Fun**

-   🎯 Number guessing game (1-10)
-   🎲 Dice rolling with custom sides
-   🪙 Coin flipping
-   🎱 Magic 8-ball style questions

</td>
</tr>
</table>

---

## 📋 Requirements

<div align="center">

| Requirement         | Version              | Purpose              |
| ------------------- | -------------------- | -------------------- |
| 🐍 **Python**       | 3.8+                 | Core runtime         |
| 🎮 **Discord.py**   | 2.0+                 | Discord integration  |
| 🤖 **Google Genai** | Latest               | AI processing        |
| 📦 **Dependencies** | See requirements.txt | Additional libraries |

</div>

---

## ⚙️ Setup

### 🚀 **Quick Start**

```bash
# 1️⃣ Clone the repository
git clone https://github.com/ifsvivek/LocalBot.git
cd LocalBot

# 2️⃣ Create virtual environment
python -m venv .venv

# 3️⃣ Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4️⃣ Install dependencies
pip install -r requirements.txt
```

### 🔑 **Environment Configuration**

Create a `.env` file in the root directory:

```env
# 🤖 Discord Bot Token (Required)
TOKEN=your_discord_bot_token

# 🎤 Genius API for lyrics (Optional)
GENIUS_TOKEN=your_genius_api_token

# 🧮 Wolfram Alpha for calculations (Optional)
WOLF=your_wolframalpha_api_key

# 🧠 Google Gemini AI (Required)
GOOGLE_API_KEY=your_google_gemini_api_key

# 🌤️ Weather API (Optional)
WEATHER_API_KEY=your_openweathermap_api_key
```

### ▶️ **Run the Bot**

```bash
python LocalBot.py
```

> 💡 **Tip:** The bot will show "localbot#1996 is ready and online!" when successfully started.

---

## 🎮 Commands

<details>
<summary><b>💬 Chat & AI Commands</b></summary>

| Command               | Description                   | Example                  |
| --------------------- | ----------------------------- | ------------------------ |
| `@LocalBot [message]` | 🗣️ Chat with Gemini AI        | `@LocalBot Hello there!` |
| `/calculate [query]`  | 🧮 Solve mathematical queries | `/calculate 2+2*3`       |
| `/weather [city]`     | 🌤️ Get weather information    | `/weather New York`      |

</details>

<details>
<summary><b>🎵 Music Commands</b></summary>

| Command          | Description                | Example                   |
| ---------------- | -------------------------- | ------------------------- |
| `/play [query]`  | 🎶 Play music from YouTube | `/play Bohemian Rhapsody` |
| `/stop`          | ⏹️ Stop current playback   | `/stop`                   |
| `/lyrics [song]` | 🎤 Get song lyrics         | `/lyrics Imagine Dragons` |
| `/join`          | ➕ Join voice channel      | `/join`                   |
| `/leave`         | ➖ Leave voice channel     | `/leave`                  |

</details>

<details>
<summary><b>🎲 Games & Fun Commands</b></summary>

| Command           | Description                | Example                    |
| ----------------- | -------------------------- | -------------------------- |
| `/gtn`            | 🎯 Guess the number (1-10) | `/gtn`                     |
| `/dice [sides]`   | 🎲 Roll dice               | `/dice 20`                 |
| `/flip`           | 🪙 Flip a coin             | `/flip`                    |
| `/ask [question]` | 🎱 Ask yes/no questions    | `/ask Will it rain today?` |

</details>

<details>
<summary><b>📷 Image Commands</b></summary>

| Command | Description         | Example |
| ------- | ------------------- | ------- |
| `/cat`  | 🐱 Random cat image | `/cat`  |
| `/dog`  | 🐕 Random dog image | `/dog`  |
| `/gt`   | 🖼️ GT meme image    | `/gt`   |

</details>

<details>
<summary><b>⚡ Utility Commands</b></summary>

| Command           | Description            | Example          |
| ----------------- | ---------------------- | ---------------- |
| `/purge [amount]` | 🗑️ Delete messages     | `/purge 10`      |
| `$clear [amount]` | 🧹 Clear DM messages   | `$clear 5`       |
| `$clear_history`  | 💾 Reset chat memory   | `$clear_history` |
| `$pin`            | 📌 Pin replied message | `$pin`           |

</details>

---

## 🛠️ Development

<div align="center">

### 🏗️ **Tech Stack**

| Technology           | Purpose              | Version   |
| -------------------- | -------------------- | --------- |
| 🐍 **Python**        | Core Language        | 3.8+      |
| 🎮 **Discord.py**    | Discord Integration  | 2.0+      |
| 🤖 **Google Gemini** | AI Processing        | 2.5-Flash |
| 🎵 **yt-dlp**        | YouTube Integration  | Latest    |
| 🧮 **Wolfram Alpha** | Mathematical Queries | API v2    |
| 🎤 **Genius API**    | Lyrics Fetching      | v1        |

### 🔄 **Key Features**

-   💾 Memory-persistent conversations
-   🔗 Multiple API integrations
-   ⚡ Async/await architecture
-   🛡️ Error handling & logging

</div>

---

## 📜 License

<div align="center">

**MIT License** © 2025 LocalBot

This project is licensed under the MIT License - see the [`LICENSE`](./LICENSE) file for details.

_Feel free to use, modify, and distribute this project as per the license terms._

</div>

---

## 🤝 Contributing

<div align="center">

### 🚀 **Get Involved**

We welcome contributions! Here's how you can help:

| Type                      | Description                         |
| ------------------------- | ----------------------------------- |
| 🐛 **Bug Reports**        | Found a bug? Open an issue!         |
| 💡 **Feature Requests**   | Have an idea? We'd love to hear it! |
| 🔧 **Code Contributions** | Submit a Pull Request               |
| 📚 **Documentation**      | Help improve our docs               |

### 📋 **Contribution Process**

1. 🍴 **Fork** the repository
2. 🌿 **Create** a feature branch
3. 💻 **Make** your changes
4. ✅ **Test** thoroughly
5. 📝 **Submit** a Pull Request

</div>

---

<div align="center">

### 🌟 **Star this repo if you found it helpful!**

Made with ❤️ by Vivek Sharma

</div>
