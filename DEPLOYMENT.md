# 🛠️ Snipers Bot – Developer Guide (For Beginners!)

Welcome! This guide will help you understand, run, and contribute to the **Snipers Bot**—even if you’ve never built a Discord bot before.

> 💡 **You don’t need to be an expert.** Just know basic Python and be willing to learn!

---

## 📁 Project Structure (What’s in the folder?)

Here’s what everything does:

```
Snipers-bot/
├── main.py                 # 🚪 The "front door" — starts the bot
├── config.py               # 🔑 Loads secrets (like your bot token)
├── .env.example            # 📝 Template for your secret settings
├── requirements.txt        # 📦 List of Python tools the bot needs
├── README.md               # 📘 User guide (for people who want to use the bot)
├── DEVELOPMENT.md          # 🧑‍💻 This file!
│
├── core/                   # ⚙️ The bot’s engine
│   ├── bot.py              # Main bot logic + loads features
│   └── database.py         # Talks to the PostgreSQL database
│
├── cogs/                   # 🧩 Features (like casino, contracts, etc.)
│   ├── contracts.py        # Assign & track work
│   ├── casino.py           # 7 fun games!
│   ├── jokes.py            # Tells jokes
│   └── ...                 # Other features
│
├── models/                 # 🧾 Data templates (like user profiles)
├── utils/                  # 🧰 Helpful tools (logging, random numbers)
├── services/               # 💼 Business logic (e.g., making receipts)
├── migrations/             # 🗃️ Database setup file (`init.sql`)
├── Dockerfile              # 🐳 For running in containers
└── docker-compose.yml      # 🐳 Runs bot + database together
```

---

## 🛠️ How to Set Up for Development

### Step 1: Install Prerequisites

You’ll need:
- **Python 3.9 or newer** → [Download here](https://www.python.org/downloads/)
- **PostgreSQL 14+** → [Download here](https://www.postgresql.org/download/)
- A **Discord bot token** → [Get one here](https://discord.com/developers/applications)

> 💡 Don’t worry—both Python and PostgreSQL are free!

---

### Step 2: Get the Code

Open your terminal (Command Prompt / PowerShell / Terminal) and run:

```bash
git clone https://github.com/pyhcho099/Snipers-bot.git
cd Snipers-bot
```

> 🔍 **No `git`?** Download the ZIP from GitHub and extract it.

---

### Step 3: Install Python Packages

Run these commands **one by one**:

```bash
# Create a safe space for the bot (recommended)
python -m venv venv

# Turn on the safe space
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

✅ You should see no errors. If you do (especially in Asia), try:

```bash
pip install discord.py asyncpg python-dotenv Pillow aiohttp pydantic python-dateutil
```

---

### Step 4: Set Up the Database

1. Open **pgAdmin** or your terminal.
2. Create a new database called `snipers`.
3. Run this in your terminal:

```bash
psql -d snipers -f migrations/init.sql
```

> This creates all the tables (users, contracts, etc.).

---

### Step 5: Configure Your Bot

1. Copy `.env.example` to a new file called `.env`:

```bash
cp .env.example .env        # Mac/Linux
copy .env.example .env      # Windows
```

2. Open `.env` in a text editor and fill in:

```env
DISCORD_TOKEN=your_bot_token_from_discord
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/snipers
GUILD_ID=your_discord_server_id
CASINO_REAL=1
```

> 🔐 **Never share `.env` or commit it to GitHub!** It’s already in `.gitignore`.

---

### Step 6: Enable Discord Bot Intents

In the [Discord Developer Portal](https://discord.com/developers/applications):
1. Go to your bot.
2. Under **Bot → Privileged Gateway Intents**, enable:
   - ✅ **SERVER MEMBERS INTENT**
   - ✅ **MESSAGE CONTENT INTENT**

> Without these, the bot won’t see messages or users!

---

### Step 7: Run the Bot!

In your terminal (with the virtual environment still active):

```bash
python main.py
```

✅ If you see:
```
🗡️ Snipers Bot#1234 is operational!
```
…you did it! 🎉

Now go to your Discord server and try `/balance` or `/joke`.

---

## 🧩 How the Bot Works (Simple Explanation)

### 1. **Cogs = Features**
Each file in `cogs/` is a feature:
- `casino.py` → handles `/coinflip`, `/slots`, etc.
- `contracts.py` → handles `/assign`, `/submit`

They’re like **plugins**—you can turn them on/off.

### 2. **Database = Memory**
The bot uses **PostgreSQL** to remember:
- Who has how many coins
- Active contracts
- Bounties, loans, etc.

All money changes happen inside **transactions** (so no one can cheat!).

### 3. **Commands = Slash Commands**
All commands start with `/` (e.g., `/daily`).  
They’re defined with `@app_commands.command()`.

Example:
```python
@app_commands.command(name="ping", description="Check bot latency")
async def ping(self, interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")
```

---

## ➕ How to Add a New Command (Step-by-Step)

Let’s add a `/daily` reward command.

### Step 1: Create `cogs/economy.py`

```python
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Get 100 coins every 24 hours")
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Shows "bot is thinking..."

        user_id = str(interaction.user.id)
        async with self.bot.db.acquire() as conn:
            # Check if user exists
            user = await conn.fetchrow(
                "SELECT id, coins FROM users WHERE discord_id = $1",
                user_id
            )
            if not user:
                await interaction.followup.send("❌ You’re not registered! Talk to an admin.")
                return

            # Check last daily claim
            last_daily = await conn.fetchval(
                "SELECT metadata->>'last_daily' FROM user_preferences WHERE user_id = $1",
                user['id']
            )

            if last_daily:
                last_time = datetime.fromisoformat(last_daily)
                if datetime.now() - last_time < timedelta(hours=24):
                    # Still on cooldown
                    wait_time = timedelta(hours=24) - (datetime.now() - last_time)
                    hours, remainder = divmod(wait_time.seconds, 3600)
                    minutes = remainder // 60
                    await interaction.followup.send(f"⏰ Wait {hours}h {minutes}m!")
                    return

            # Give reward
            reward = 100
            new_balance = user['coins'] + reward

            async with conn.transaction():
                # Update coins
                await conn.execute(
                    "UPDATE users SET coins = $1 WHERE id = $2",
                    new_balance, user['id']
                )
                # Log transaction
                await conn.execute(
                    "INSERT INTO transactions (user_id, type, amount, balance_after, reason) "
                    "VALUES ($1, 'daily', $2, $3, 'daily_reward')",
                    user['id'], reward, new_balance
                )
                # Save last claim time
                await conn.execute("""
                    INSERT INTO user_preferences (user_id, metadata)
                    VALUES ($1, jsonb_build_object('last_daily', $2::text))
                    ON CONFLICT (user_id) DO UPDATE
                    SET metadata = jsonb_set(
                        COALESCE(user_preferences.metadata, '{}'::jsonb),
                        '{last_daily}',
                        to_jsonb($2::text)
                    )
                """, user['id'], datetime.now().isoformat())

            await interaction.followup.send(f"✅ **+{reward} coins!** New balance: {new_balance}")

async def setup(bot):
    await bot.add_cog(Economy(bot))
```

### Step 2: Load the Cog

In `core/bot.py`, find the list of cogs and add `'cogs.economy'`.

### Step 3: Restart the Bot

Stop (`Ctrl+C`) and run `python main.py` again.

Now try `/daily` in Discord!

---

## 🐞 Debugging Tips

### Problem: “Command not found”
- Wait 1 hour (global commands take time), **or**
- Set `GUILD_ID` in `.env` for instant sync.

### Problem: “Database connection failed”
- Is PostgreSQL running? (Check pgAdmin or run `pg_ctl status`)
- Is the `DATABASE_URL` correct?

### Problem: “Module not found”
- Did you activate the virtual environment?
- Did you run `pip install -r requirements.txt`?

---

## 🧪 Testing Your Code

1. Use a **test Discord server** (don’t test on your main one!).
2. Create a **separate bot** in the Developer Portal for testing.
3. Use a **test database** (`snipers_test`).

---

## 🤝 How to Contribute

1. Fork the repo on GitHub.
2. Make your changes.
3. Test locally.
4. Open a **Pull Request** with:
   - What you changed
   - Why it’s useful
   - Screenshots (if UI-related)

---

## 📚 Helpful Resources

- [discord.py Docs](https://discordpy.readthedocs.io/)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [Discord API Docs](https://discord.com/developers/docs/intro)

---

## ❓ Need Help?

- Open an **Issue** on GitHub
- Email: your-email@example.com
- Join our Discord support server (link)

---

**Happy coding! You’ve got this! 💪**