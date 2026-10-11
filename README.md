# 🤖 Koro

**A customizable AI-powered Discord chatbot with multiple personalities and persistent server memory.**

Koro is an AI-powered Discord bot built with Python, `discord.py`, and OpenRouter. It combines natural AI conversations, personality switching, useful Discord utilities, and a persistent memory system that can retrieve relevant context from previous server conversations.

Designed to be lightweight and customizable, Koro can run locally or on compatible hosting platforms.

[Features](#-features) · [Installation](#-installation) · [Commands](#-commands) · [Personalities](#-personality-modes) · [Memory](#-persistent-server-memory) · [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### 💬 AI-powered conversations
- Chat naturally with Koro using `!chat`.
- Powered by OpenRouter and compatible AI models configured in the project.
- Switch between different personality modes.
- Use relevant stored server messages as context for AI responses.
- Split long AI responses into Discord-compatible message chunks.

### 🎭 Multiple personalities
Choose between four personality modes:

- 🧠 **Normal** — Friendly, balanced conversations.
- 💀 **Brainrot** — Chaotic internet humour and memes.
- 🏛️ **Socrates** — Philosophical questions and thoughtful discussion.
- 🎲 **Random** — Selects a personality at random for each conversation.

### 🧠 Persistent server memory
- Store eligible Discord messages in an SQLite database.
- Import accessible historical messages from eligible channels.
- Retain stored memory across bot restarts when persistent storage is available.
- Keep memories separated by Discord server.
- Search historical conversations for relevant context.
- Track historical import progress.
- Respect the requester's channel access when retrieving memories.

### ⚙️ Discord utilities
- Latency and uptime checks.
- Server and member information.
- Dice rolls and coin flips.
- Joke command.
- Feedback and support commands.
- Bot information and invitation links.
- Slash-command support.

### ☁️ Hosting and customization
- Run locally on a compatible Python environment.
- Deploy to compatible free or paid hosting platforms.
- Configure Discord and OpenRouter credentials using environment variables.
- Customize personality prompts and AI behavior.

---

## 🛠️ Built With

| Technology | Purpose |
|---|---|
| Python 3.11+ | Core programming language |
| discord.py | Discord bot integration |
| OpenRouter API | AI model access |
| python-dotenv | Environment-variable loading |
| SQLite | Persistent memory storage |
| SQLite FTS5 | Full-text message search, where supported |
| asyncio | Asynchronous operations |

Use a Python version supported by your installed dependencies and hosting environment.

---

## 📂 Project Structure

The main application files include:

```text
koro-ai/
├── bot.py
├── ai.py
├── memory.py
├── requirements.txt
├── .env
├── normal.txt
├── brainrot.txt
├── socrates.txt
├── data/
│   └── koro_memory.sqlite3
├── .gitignore
├── LICENSE
└── README.md
```

*Note: The structure above documents the expected memory-related additions. Your actual repository may contain additional files or a different database location.*

| File | Purpose |
|---|---|
| `bot.py` | Discord bot, commands, and event handling |
| `ai.py` | AI response integration |
| `memory.py` | Persistent memory, storage, and search |
| `requirements.txt` | Python dependencies |
| `normal.txt` | Normal personality configuration |
| `brainrot.txt` | Brainrot personality configuration |
| `socrates.txt` | Socrates personality configuration |
| `.env` | Local secrets and environment variables |
| `data/koro_memory.sqlite3` | Default memory database path, if configured this way |

**Security note:** Never commit `.env`, real API keys, or a database containing private server messages to a public repository.

---

## 🚀 Installation

### Prerequisites

Before installing Koro, make sure you have:

- Python 3.11 or a compatible newer version.
- Git, if you want to clone the repository.
- A Discord application and bot token.
- An OpenRouter API key.
- A Discord server where you have permission to add bots.

### 1. Clone the repository

```bash
git clone https://github.com/Pranab-dev/koro-ai.git
cd koro-ai
```

### 2. Create a virtual environment (recommended)

**Windows — PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

Replace the placeholders with your actual credentials.

**Never share your bot token or API key.** If either is accidentally published, revoke or rotate it immediately.

### 5. Configure your Discord bot

Open the [Discord Developer Portal](https://discord.com/developers/applications).

1. Create an application or select your existing Koro application.
2. Open the **Bot** settings and obtain your bot token.
3. Enable **Message Content Intent** if Koro uses prefix commands or reads message content.
4. Configure the application's installation settings.
5. Invite Koro to your server with the required permissions.

Typical permissions include:

- View Channels
- Send Messages
- Read Message History
- Use Application Commands

Grant additional permissions only when required by the enabled features.

### 6. Start Koro

```bash
python bot.py
```

If everything is configured correctly, Koro should connect to Discord and synchronize its application commands where configured.

---

## 💬 Commands

Koro supports the following commands from the current project documentation.

| Command | Description |
|---|---|
| `!chat <message>` | Chat with Koro |
| `/ping` | Check bot latency |
| `/mode` | Change Koro's personality |
| `/status` | Display the current personality mode |
| `/about` | Show information about Koro |
| `/userinfo` | Display user information |
| `/uptime` | Show how long Koro has been running |
| `/support` | Get support information |
| `/server` | Display server information |
| `/membercount` | Show the server's member count |
| `/joke` | Tell a joke |
| `/help` | Display available commands |
| `/invite` | Get Koro's invitation link |
| `/feedback` | Submit feedback |
| `/dice` | Roll a dice |
| `/coinflip` | Flip a coin |

### Memory management

The memory system also provides management functionality for checking status, disabling memory, and clearing stored data.

The exact command names and arguments depend on the implementation currently deployed. Check Koro's registered application commands and the latest source code for the authoritative syntax.

---

## 🎭 Personality Modes

### 🧠 Normal

Friendly, balanced conversations suitable for everyday questions and general assistance.

### 💀 Brainrot

Chaotic internet humour, memes, and a more unserious conversational style.

### 🏛️ Socrates

A philosophical personality focused on questions, reasoning, and thoughtful discussion.

### 🎲 Random

Randomly selects one of the available personality modes for each conversation.

Use `/mode` to change the personality and `/status` to check the currently selected mode.

---

## 🧠 Persistent Server Memory

Koro's memory update adds persistent storage and historical context retrieval to its AI conversations.

Instead of relying exclusively on the current message, Koro can search eligible stored messages and use relevant results as additional context for an AI response.

### How it works

**1. Historical imports**

When memory is enabled, Koro can import accessible message history from eligible channels. Import progress is tracked so unfinished imports can resume.

**2. Live collection**

New eligible messages can be stored as Discord message events occur, rather than requiring the bot to repeatedly download the entire history.

**3. Persistent storage**

Messages and associated metadata are stored in SQLite and can remain available after restarts, provided the database file is preserved.

**4. Context retrieval**

When a user asks a question, Koro searches stored messages and can supply relevant results to the AI backend.

**5. Server separation**

Memory retrieval is scoped to the current Discord server. Results should also be limited to channels the requesting user can currently access.

### Database

The default database path in the documented implementation is:

```text
data/koro_memory.sqlite3
```

The `KORO_MEMORY_DB_PATH` environment variable can be used to override the path if the application is configured to support it.

Keep the database on persistent storage when hosting Koro. A temporary or ephemeral filesystem may erase stored memory after a restart or redeployment.

### Import performance

Import duration depends on:

- Historical message volume.
- Discord API rate limits.
- Channel and thread permissions.
- Network conditions.
- Database performance.

A completed import means the importer finished processing that channel; it does not guarantee that every historical message was accessible or eligible.

---

## 🔐 Privacy and Security

Koro's persistent memory may contain messages written by Discord server members. Server administrators should understand how collection and retrieval work before enabling the feature.

Recommended practices:

- Notify members before enabling historical imports or automatic collection.
- Explain what information is stored and how it is used.
- Document the retention policy.
- Provide a clear way to disable collection and clear stored memory.
- Exclude private and staff-only channels by default unless collection is explicitly appropriate and authorized.
- Restrict memory search to channels the requesting user can access.
- Keep credentials and database backups secure.
- Never commit conversation databases or secrets to a public repository.

**Important:** Removing a message from Discord does not necessarily remove a previously stored copy from Koro's database. Deletion and retention behavior should be verified and explained to server administrators.

---

## ☁️ Hosting

Koro can run locally or on compatible Python hosting platforms.

For persistent memory, choose a host that supports durable storage. If the hosting platform deletes local files during restarts or redeployments, the SQLite database may be lost.

For production use:

- Configure secrets through environment variables.
- Use persistent storage for the database.
- Back up memory before deployments or schema changes.
- Monitor the bot's logs.
- Check Discord channel permissions if commands fail.
- Verify the AI provider's API credentials and usage limits.

Free hosting availability, uptime, storage, and resource limits depend on the provider.

---

## 🛠️ Troubleshooting

### Koro does not start

- Confirm the bot token is correct.
- Verify all dependencies are installed.
- Check the Python version.
- Read the terminal output for missing modules or configuration errors.

### AI responses fail

- Verify `OPENROUTER_API_KEY`.
- Check the configured model and endpoint in `ai.py`.
- Review provider errors and usage limits.
- Confirm the backend returns a response format expected by Koro.

### `403 Forbidden` or `Missing Access`

- Verify Koro can view the channel.
- Check category and channel-specific permission overrides.
- Ensure the bot has permission to send messages and read history where required.
- Confirm the channel or thread still exists and is accessible.

Exception handling can prevent an unhandled command error, but it cannot restore missing permissions.

### Memory database errors

- Check that the database path is writable.
- Confirm all required database tables are initialized.
- Verify that the deployed code includes the latest schema.
- Back up existing data before manually changing the database.

### Historical imports are slow

Large servers may take considerable time to import. Check the logs and saved import progress before resetting the importer or deleting database records.

---

## 🗺️ Roadmap

| Feature | Status |
|---|---|
| Slash commands | ✅ Implemented |
| Multiple personality modes | ✅ Implemented |
| Multiple AI models | ✅ Supported through the configured AI integration |
| Improved moderation | ✅ Existing project feature |
| Persistent server memory | ✅ Implemented |
| Historical message imports | ✅ Implemented |
| Image generation | ⬜ Planned |
| Web dashboard | ⬜ Planned |

The roadmap reflects the current project direction and may change as development continues.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a branch for your feature or fix.
3. Make your changes.
4. Test the affected functionality.
5. Open a pull request describing your changes.

Ideas for new personality modes, memory improvements, AI integrations, bug fixes, and documentation are welcome.

Please do not include API keys, bot tokens, private messages, or production memory databases in pull requests or issue reports.

---

## 🐛 Reporting Issues

When reporting a bug, include:

- A description of the issue.
- Steps to reproduce it.
- Relevant error logs with secrets removed.
- Your operating system and Python version.
- Whether the issue affects chat, personality modes, memory, imports, or Discord permissions.

Never post your bot token or API key in a public issue.

---

## 📄 License

Koro is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for the full license text.

---

## 👨‍💻 Author

**Pranab Mukherjee**

GitHub: [@Pranab-dev](https://github.com/Pranab-dev)

Repository: [Pranab-dev/koro-ai](https://github.com/Pranab-dev/koro-ai)

---

## ⭐ Support Koro

If you enjoy Koro, consider giving the repository a ⭐, reporting bugs, or contributing improvements.

Every contribution helps the project grow.

**Made with ❤️ by Pranab Mukherjee.**
