### ✅ `README.md`

```markdown
# 🗡️ Snipers Bot

A comprehensive Discord bot for managing scanlation teams with contracts, economy, casino games, and entertainment features. Built with `discord.py` and PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-2.3%2B-blue.svg)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

### 📜 Contract Management
- **Assign contracts** to team members with roles (RP, TL, PR, CLRD, TS, QC, Uploader)
- **Submit work** with proof URLs
- **Track progress** with deadlines and status
- **Automatic rewards** – coins paid upon completion
- **Full audit trail** – immutable transaction logs

### 💰 Economy System
- **Coin-based rewards** for completed work
- **User profiles** with balance, XP, rank, and stats
- **Transaction history** – every coin movement tracked
- **Admin controls** – add/remove coins, force complete contracts

### 🎰 Casino Games (7 Games)
- **Coinflip** – Double or nothing
- **Blackjack** – Interactive with Hit/Stand buttons
- **Roulette** – Bet on red/black/green/numbers (35x payouts!)
- **Dice** – Predict over7/under7/exactly7
- **Crash** – Multiplier game with real-time cashout
- **Slots** – 3-reel slot machine with jackpots
- **Lottery** – Buy tickets for 500 coin prizes
- **Provably fair RNG** – verifiable randomness

### 🎭 Entertainment
- **JokeAPI integration** – safe and uncensored modes
- **User preferences** – set default joke mode
- **Multi-joke** – fetch 1–5 jokes at once
- **Joke ratings** – react with 😂😐😔 to rate
- **NSFW detection** – blocks inappropriate jokes in safe channels

### 🎯 Bounty System
- **Place bounties** on users (min 100 coins)
- **Claim bounties** with evidence
- **Admin resolution** – approve/reject claims
- **Automatic payouts** when approved

### 💸 Additional Features
- **Loan system** – request loans with interest (if enabled)
- **Room creation** – temporary private channels (10 coins/hour)
- **Help system** – comprehensive command reference
- **Ping checker** – monitor bot latency

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/))
- **Discord Bot Token** ([Get one](https://discord.com/developers/applications))

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/pyhcho099/Snipers-bot.git
cd Snipers-bot
```

#### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**If you get network errors (Asia region):**
```bash
pip install discord.py asyncpg python-dotenv Pillow aiohttp pydantic python-dateutil
```

#### 3. Setup Database

```bash
# Create database
createdb snipers

# Import schema (automatic on first run, or manual):
psql -d snipers -f migrations/init.sql
```

#### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your values
nano .env
```

**Required variables:**
```env
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@localhost:5432/snipers
GUILD_ID=your_server_id_here
CASINO_REAL=1
```

#### 5. Setup Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to **Bot** section → Add Bot
4. Copy token to `.env` file
5. Enable these **Privileged Gateway Intents**:
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
6. Go to **OAuth2 → URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Administrator` (or customize)
7. Use generated URL to invite bot to your server

#### 6. Run the Bot

```bash
python main.py
```

**Expected output:**
```
[2025-11-01 11:30:00] [INFO] ✅ Database pool created
[2025-11-01 11:30:01] [INFO] ✅ Loaded: cogs.contracts
[2025-11-01 11:30:02] [INFO] ✅ Commands synced to guild 123456789
[2025-11-01 11:30:03] [INFO] 🗡️ Snipers Bot#1234 is operational!
```

---

## 📚 Commands Reference

### 📜 Contract Management

| Command | Description | Example |
|--------|-------------|--------|
| `/assign` | Assign a contract to a user | `/assign @user RP "One Piece" 1050 500` |
| `/submit` | Submit completed work | `/submit 42 https://proof.url "Done!"` |
| `/balance` | Check your stats and coins | `/balance` |

### 🎯 Bounties

| Command | Description | Example |
|--------|-------------|--------|
| `/bounty-place` | Place bounty on user | `/bounty-place @user 1000 "Reason"` |
| `/bounty-claim` | Claim a bounty | `/bounty-claim 5 https://evidence.url` |
| `/bounty-list` | List all open bounties | `/bounty-list` |
| `/bounty-resolve` | [ADMIN] Approve/reject claim | `/bounty-resolve 5 approve` |

### 🎰 Casino

| Command | Description | Min Bet |
|--------|-------------|--------|
| `/coinflip <bet>` | Flip a coin | 1 coin |
| `/blackjack <bet>` | Play blackjack | 10 coins |
| `/roulette <bet> <choice>` | Bet on roulette | 1 coin |
| `/dice <bet> <prediction>` | Roll dice | 1 coin |
| `/crash <bet>` | Multiplier crash game | 10 coins |
| `/slots <bet>` | Slot machine | 1 coin |
| `/lottery <tickets>` | Buy lottery tickets (1–10) | 100 coins/ticket |

### 🎭 Entertainment

| Command | Description |
|--------|-------------|
| `/joke [category]` | Get a joke (respects preferences) |
| `/uncensoredjoke [category]` | Get unfiltered joke |
| `/multijoke <count> [category]` | Get multiple jokes (1–5) |
| `/preferences` | Set joke preferences (safe/uncensored) |
| `/ratejoke` | View joke rating info |

### 💸 Other

| Command | Description |
|--------|-------------|
| `/loan-request <amount> <days> [interest]` | Request a loan |
| `/room-create <name> <hours>` | Create private room (10 coins/hour) |
| `/help` | Show all commands |
| `/ping` | Check bot latency |

### ⚙️ Admin Only

| Command | Description |
|--------|-------------|
| `/addcoins <user> <amount>` | Add/remove coins |
| `/forcecomplete <contract_id> <reason>` | Force complete contract |

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

### Environment Variables (Docker)

Set these in `.env` or `docker-compose.yml`:
- `DISCORD_TOKEN` – Your bot token
- `DATABASE_URL` – PostgreSQL connection string
- `GUILD_ID` – Your Discord server ID
- `CASINO_REAL` – Enable casino (`1` = on, `0` = off)
- `LOAN_SYSTEM` – Enable loans (`1` = on, `0` = off)

---

## 🌐 Cloud Deployment

### Replit (Easiest)

1. Fork this repo to your GitHub
2. Go to [Replit](https://replit.com)
3. Create Repl → Import from GitHub
4. Add Secrets (Environment):
   - `DISCORD_TOKEN`
   - `DATABASE_URL` (use Replit's PostgreSQL)
   - `GUILD_ID`
5. Click Run!

### Railway.app (Production)

1. Connect [Railway](https://railway.app) to GitHub
2. Import `Snipers-bot` repo
3. Add PostgreSQL service
4. Set environment variables
5. Deploy automatically on push

### Render.com (Free)

1. Sign up at [Render](https://render.com)
2. New Web Service → Connect GitHub repo
3. Add PostgreSQL database
4. Set environment variables
5. Deploy

> **Note:** Free tier sleeps after inactivity. Use UptimeRobot to keep alive.

---

## 🛠️ Troubleshooting

### Bot not responding to commands

**Check:**
- Bot is online in Discord (green circle)
- Bot has `applications.commands` permission
- Commands are synced (check console for "Commands synced")
- `GUILD_ID` is correct (or remove for global commands)

**Fix:**
```bash
# In Discord, type:
/
# Wait 1 hour for global sync, or set GUILD_ID for instant sync
```

### Database connection errors

**Error:** `database "snipers" does not exist`

**Fix:**
```bash
createdb snipers
psql -d snipers -f migrations/init.sql
```

**Error:** `connection refused`

**Fix:**
- Verify PostgreSQL is running: `pg_ctl status`
- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`

### Import errors (ModuleNotFoundError)

**Error:** `No module named 'discord'`

**Fix:**
```bash
pip install -r requirements.txt
# Or individually:
pip install discord.py asyncpg python-dotenv Pillow aiohttp pydantic
```

### Network/pip install issues (Asia region)

**Fix:**
```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com discord.py asyncpg python-dotenv Pillow aiohttp pydantic python-dateutil
```

---

## 📊 Database Schema

The bot uses **9 tables**:

- `users` – User profiles with coins/XP/rank
- `contracts` – Work assignments with rewards
- `contract_submissions` – Proof submissions
- `bounties` – User bounties
- `loans` – Loan records (if enabled)
- `transactions` – Immutable audit log
- `rooms` – Temporary channels
- `logs` – System event logs
- `user_preferences` – User settings (joke modes)

**All tables use PostgreSQL enums** for type safety.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/pyhcho099/Snipers-bot/issues)
- **Discord:** Join our support server (link)
- **Email:** your-email@example.com

---

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) – Discord API wrapper
- [JokeAPI](https://jokeapi.dev/) – Joke data source
- [PostgreSQL](https://www.postgresql.org/) – Database
- [asyncpg](https://github.com/MagicStack/asyncpg) – Fast async PostgreSQL driver

---

**Made with ❤️ by the Snipers Team**
```