<div align="center">

# 🤖 LocalBot

_A powerful Discord bot powered by Cerebras AI_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Cerebras AI](https://img.shields.io/badge/Cerebras-AI-ff69b4.svg)](https://cerebras.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

_Natural conversations • Games & Entertainment • Native Tool Calling • Utility functions_

[Features](#-features) • [Setup](#️-setup) • [Commands](#-commands) • [Contributing](#-contributing)

</div>

---

## ✨ Features

-   🗣️ **Native Tool Calling**: Powered by Cerebras with robust JSON schema integration
-   🧠 **Dual Model Fallback**: Primary **gpt-oss-120b** with secondary **llama-3.3-70b**
-   💭 **Smart Context**: Persistent conversation memory per server/DM
-   🌤️ **Utility Tools**: Weather updates, mathematical calculations via Wolfram Alpha
-   🎮 **Games & Fun**: GT pictures, coin flips, dice rolls, and guessing games
-   🖼️ **Media Integration**: Random cat/dog images and meme fetching from Reddit
-   ⚙️ **Modern Architecture**: Fully asynchronous and optimized for low-latency AI responses

---

## 📋 Requirements

<div align="center">

| Requirement        | Version              | Purpose              |
| ------------------ | -------------------- | -------------------- |
| 🐍 **Python**       | 3.10+                | Core runtime         |
| 🎮 **Py-Cord**      | 2.0+                 | Discord integration  |
| 🧠 **Cerebras SDK** | Latest               | AI processing        |
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

# 🧠 Cerebras AI API Key (Required)
CEREBRAS_API_KEY=your_cerebras_api_key

# 🧮 Wolfram Alpha for calculations (Optional)
WOLF=your_wolframalpha_api_key

# 🌤️ Weather API (Optional)
WEATHER_API_KEY=your_openweathermap_api_key
```

### ▶️ **Run the Bot**

```bash
python LocalBot.py
```

---

## 🎮 Commands

<details>
<summary><b>💬 Chat & AI Commands</b></summary>

| Command               | Description                  | Example                  |
| --------------------- | ---------------------------- | ------------------------ |
| `@LocalBot [message]` | 🗣️ Chat with Cerebras AI      | `@LocalBot Hello there!` |
| `/calculate [query]`  | 🧮 Solve mathematical queries | `/calculate 2+2*3`       |
| `/weather [city]`     | 🌤️ Get detailed weather info  | `/weather Bangalore`     |
| `/whats_new`          | 🆕 Show recent bot updates    | `/whats_new`             |

</details>

<details>
<summary><b>🎲 Games & Fun Commands</b></summary>

| Command           | Description                | Example                    |
| ----------------- | -------------------------- | -------------------------- |
| `/gtn`            | 🎯 Guess the number (1-10)  | `/gtn`                     |
| `/dice [sides]`   | 🎲 Roll dice                | `/dice 20`                 |
| `/flip`           | 🪙 Flip a coin              | `/flip`                    |
| `/ask [question]` | 🎱 Ask yes/no questions     | `/ask Will it rain today?` |
| `/meme`           | 😂 Get a random Reddit meme | `/meme`                    |

</details>

<details>
<summary><b>📷 Media Commands</b></summary>

| Command | Description        | Example |
| ------- | ------------------ | ------- |
| `/cat`  | 🐱 Random cat image | `/cat`  |
| `/dog`  | 🐕 Random dog image | `/dog`  |
| `/gt`   | 🖼️ GT meme image    | `/gt`   |

</details>

<details>
<summary><b>⚡ Utility Commands</b></summary>

| Command            | Description              | Example           |
| ------------------ | ------------------------ | ----------------- |
| `/purge [amount]`  | 🗑️ Delete server messages | `/purge 10`       |
| `/serverinfo`      | ℹ️ Get server details     | `/serverinfo`     |
| `/userinfo [user]` | 👤 Get user information   | `/userinfo @user` |
| `$clear [amount]`  | 🧹 Clear DM bot messages  | `$clear 5`        |
| `$clear_history`   | 💾 Reset chat memory      | `$clear_history`  |
| `$pin`             | 📌 Pin replied message    | `$pin`            |

</details>


## 🛠️ Tech Stack

<div align="center">

| Technology          | Purpose              | Version |
| ------------------- | -------------------- | ------- |
| 🐍 **Python**        | Core Language        | 3.10+   |
| 🎮 **Py-Cord**       | Discord Integration  | 2.0+    |
| 🧠 **Cerebras AI**   | AI Processing        | Native  |
| 🔗 **LangChain**     | Memory Management    | 0.1+    |
| 🧮 **Wolfram Alpha** | Mathematical Queries | API v1  |

</div>

---

## 📜 License

<div align="center">

**MIT License** © 2026 LocalBot

This project is licensed under the MIT License - see the [`LICENSE`](./LICENSE) file for details.

</div>

---

<div align="center">

### 🌟 **Star this repo if you found it helpful!**

Made with ❤️ by Vivek Sharma

</div>
