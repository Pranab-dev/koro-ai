# 🤖 Koro AI

A customizable AI-powered Discord chatbot built with **Python**, **discord.py**, and **OpenRouter**.

Koro AI can chat naturally, switch between multiple personalities, and run 24/7 on compatible hosting platforms.

---

## ✨ Features

* 💬 AI-powered conversations
* 🎭 Multiple personality modes

  * Normal
  * Brainrot
  * Socrates
  * Random
* ⚡ Fast responses
* ☁️ Compatible with free and paid Python hosting
* 🔧 Simple configuration using environment variables
* 🪶 Lightweight and beginner-friendly codebase

---

## 🛠️ Built With

* Python 3.11+
* discord.py
* OpenRouter API
* python-dotenv

---

## 📂 Project Structure

```text
koro-ai/
│── bot.py
│── ai.py
│── requirements.txt
│── .env
│── normal.txt
│── brainrot.txt
│── socrates.txt
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Pranab-dev/koro-ai.git
cd koro-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

### 4. Start the bot

```bash
python bot.py
```

---

## 💬 Commands

| Command           | Description                       |
| ----------------- | --------------------------------- |
| `!chat <message>` | Chat with Koro                    |
| `!ping`           | Check if the bot is online        |
| `!koro normal`    | Switch to Normal mode             |
| `!koro brainrot`  | Switch to Brainrot mode           |
| `!koro socrates`  | Switch to Socrates mode           |
| `!koro random`    | Enable random personalities       |
| `!status`         | View the current personality mode |

---

## 🎭 Personality Modes

### 🧠 Normal

Friendly and balanced conversations.

### 💀 Brainrot

Chaotic internet humour and memes.

### 🏛️ Socrates

Responds using philosophical questions and thoughtful discussion.

### 🎲 Random

Randomly selects one of the available personalities for each conversation.

---

## ⚙️ Environment Variables

| Variable             | Description             |
| -------------------- | ----------------------- |
| `DISCORD_TOKEN`      | Your Discord bot token  |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

---

## 🤝 Contributing

Contributions are welcome!

If you have ideas for new personalities, features, or bug fixes, feel free to open an issue or submit a pull request.

---

## 📝 Roadmap

* [ ] Conversation memory
* [ ] Slash commands
* [ ] Image generation
* [ ] Per-server settings
* [ ] Web dashboard
* [ ] More AI models
* [ ] Improved moderation

---

## ⭐ Support

If you enjoy this project, consider giving the repository a ⭐.

It helps others discover Koro AI and motivates future development.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details

---

Made with ❤️ by **Pranab**
