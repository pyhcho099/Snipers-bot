
```markdown
# 🛠️ Snipers Bot - Development Guide

Complete guide for developers contributing to or extending the Snipers Bot.

---

## 📁 Project Structure

```
Snipers-bot/
├── main.py                     # Entry point - starts bot
├── config.py                   # Environment config loader
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── README.md                  # User documentation
├── DEVELOPMENT.md             # This file
│
├── core/                      # Core bot infrastructure
│   ├── __init__.py
│   ├── bot.py                 # SnipersBot class, cog loader, event handlers
│   └── database.py            # asyncpg connection pool, query helpers
│
├── cogs/                      # Command modules (Discord cogs)
│   ├── __init__.py
│   ├── contracts.py           # /assign, /submit, /balance commands
│   ├── bounties.py            # /bounty-* commands
│   ├── casino.py              # All 7 casino games + interactive buttons
│   ├── jokes.py               # JokeAPI integration + preferences
│   ├── loans.py               # Loan system commands
│   ├── rooms.py               # Temporary room creation
│   ├── admin.py               # Admin-only commands
│   └── utility.py             # /help, /ping commands
│
├── models/                    # Data models (Pydantic)
│   ├── __init__.py
│   ├── enums.py               # ContractRole, TransactionType, etc.
│   ├── user.py                # User model
│   └── contract.py            # Contract model
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── logger.py              # Logging setup
│   ├── rng.py                 # Provably fair RNG for casino
│   └── embeds.py              # Discord embed templates
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── png_service.py         # Contract receipt PNG generation
│   └── transaction_service.py # Transaction management
│
├── migrations/                # Database schema
│   └── init.sql               # Initial schema with tables/enums
│
├── .devcontainer/             # GitHub Codespaces config (optional)
│   ├── devcontainer.json
│   └── docker-compose.dev.yml
│
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Multi-container setup
└── .gitignore                 # Git ignore rules
```

---

## 🏗️ Architecture

### **Design Patterns**

1. **Cog-based Architecture** - Commands organized by feature (contracts, casino, etc.)
2. **Service Layer** - Business logic separated from Discord commands
3. **Repository Pattern** - Database access through connection pool
4. **Dependency Injection** - Bot instance passed to cogs with database access

### **Key Components**

#### **1. Core Bot (`core/bot.py`)**

```
class SnipersBot(commands.Bot):
    - Initializes Discord client with intents
    - Loads all cogs from cogs/ directory
    - Syncs slash commands (guild or global)
    - Manages database connection pool
    - Handles bot lifecycle (startup/shutdown)
```

**Lifecycle:**
1. `__init__()` - Setup intents, prefix, database reference
2. `setup_hook()` - Load cogs, sync commands, connect database
3. `on_ready()` - Log startup, set presence
4. `close()` - Cleanup database connections

#### **2. Database (`core/database.py`)**

```
class Database:
    - Creates asyncpg connection pool (5-20 connections)
    - Runs migrations/init.sql on first start
    - Provides query helpers: fetchrow(), fetch(), execute()
    - Context manager for transactions
```

**Connection String Format:**
```
postgresql://username:password@host:port/database
```

**Transaction Safety:**
```
async with conn.transaction():
    # All queries here are atomic
    # Automatically rolls back on exception
```

#### **3. Cogs (Command Modules)**

Each cog handles a feature set:

- **contracts.py** - Contract lifecycle (assign → submit → pay)
- **casino.py** - 7 games with RNG, button interactions
- **jokes.py** - JokeAPI + user preferences + NSFW filtering
- **bounties.py** - Bounty placement/claiming/resolution
- **admin.py** - Admin tools (addcoins, forcecomplete)

**Cog Structure:**
```
class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Access to bot.db for database queries
    
    @app_commands.command(name="mycommand")
    async def my_command(self, interaction: discord.Interaction):
        # Command logic
        pass

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

---

## 🗄️ Database Design

### **Tables Overview**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User profiles | discord_id, coins, xp, rank |
| `contracts` | Work assignments | assignee_id, role, reward_amount, status |
| `bounties` | User bounties | target_id, amount, status |
| `transactions` | Audit log (immutable) | user_id, type, amount, balance_after |
| `loans` | Debt tracking | borrower_id, principal, interest_rate |
| `rooms` | Temporary channels | discord_id, owner_id, expires_at |
| `logs` | System events | type, actor_id, payload (JSONB) |
| `user_preferences` | User settings | user_id, joke_mode |

### **Important Constraints**

1. **Coins must be non-negative**: `CHECK (coins >= 0)`
2. **Bounties minimum 100**: `CHECK (amount >= 100)`
3. **Foreign keys enforce referential integrity**
4. **Indexes on frequently queried columns** (assignee_id, status, etc.)

### **Transaction Pattern**

**ALWAYS use transactions for coin operations:**

```
async with self.bot.db.acquire() as conn:
    async with conn.transaction():
        # 1. Lock user row (prevents race conditions)
        user = await conn.fetchrow(
            "SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
            str(user_id)
        )
        
        # 2. Update balance
        new_balance = user['coins'] + amount
        await conn.execute(
            "UPDATE users SET coins = $1 WHERE id = $2",
            new_balance, user['id']
        )
        
        # 3. Log transaction
        await conn.execute("""
            INSERT INTO transactions (user_id, type, amount, balance_after, reason)
            VALUES ($1, $2, $3, $4, $5)
        """, user['id'], 'earn', amount, new_balance, 'some_reason')
```

**Why?**
- `FOR UPDATE` locks the row, preventing concurrent modifications
- `async with conn.transaction()` makes all queries atomic
- Automatic rollback on exception (no partial updates)

---

## 🎮 Adding New Commands

### **Example: Add a "Daily Reward" Command**

#### 1. Create the command in appropriate cog (e.g., `cogs/economy.py`)

```
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utils.embeds import create_success_embed

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="daily", description="Claim daily reward (100 coins)")
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with self.bot.db.acquire() as conn:
            # Check last claim time
            last_claim = await conn.fetchval("""
                SELECT metadata->>'last_daily' FROM user_preferences
                WHERE user_id = (SELECT id FROM users WHERE discord_id = $1)
            """, str(interaction.user.id))
            
            if last_claim:
                last_dt = datetime.fromisoformat(last_claim)
                if datetime.now() - last_dt < timedelta(hours=24):
                    time_left = timedelta(hours=24) - (datetime.now() - last_dt)
                    await interaction.followup.send(f"⏰ Come back in {time_left.seconds // 3600}h {(time_left.seconds % 3600) // 60}m")
                    return
            
            # Give reward
            async with conn.transaction():
                user = await conn.fetchrow(
                    "SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
                    str(interaction.user.id)
                )
                
                reward = 100
                new_balance = user['coins'] + reward
                
                await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                await conn.execute("""
                    INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                    VALUES ($1, 'earn', $2, $3, 'daily_reward')
                """, user['id'], reward, new_balance)
                
                # Update last claim time
                await conn.execute("""
                    INSERT INTO user_preferences (user_id, metadata)
                    VALUES ($1, jsonb_build_object('last_daily', $2::text))
                    ON CONFLICT (user_id) DO UPDATE SET metadata = jsonb_set(
                        COALESCE(user_preferences.metadata, '{}'::jsonb),
                        '{last_daily}',
                        to_jsonb($2::text)
                    )
                """, user['id'], datetime.now().isoformat())
        
        embed = create_success_embed("Daily Reward", f"**+{reward} coins**\nBalance: {new_balance}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
```

#### 2. Register the cog in `core/bot.py`

Add `'cogs.economy'` to the cogs list in `setup_hook()`.

#### 3. Test

```
python main.py
# In Discord: /daily
```

---

## 🎰 Casino Game Development

### **RNG System (`utils/rng.py`)**

**Provably Fair Random Number Generation:**

```
class ProvablyFairRNG:
    def generate(self, client_seed: str) -> float:
        # Combines server seed + client seed + nonce
        # Returns deterministic float 0.0-1.0
        # Can be verified after the fact
```

**Usage in Games:**

```
from utils.rng import rng

# Generate random result
result = rng.generate(str(interaction.user.id))

if result >= 0.5:
    # Player wins
else:
    # Player loses
```

### **Interactive Buttons**

**Example: Blackjack Hit/Stand**

```
from discord.ui import Button, View

class BlackjackView(View):
    def __init__(self, game_data, user_id, bot):
        super().__init__(timeout=60)
        self.game_data = game_data
        self.user_id = user_id
        self.bot = bot
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
        
        # Game logic
        card = random.randint(1, 11)
        self.game_data['player_hand'].append(card)
        
        # Update message
        embed = discord.Embed(...)
        await interaction.response.edit_message(embed=embed, view=self)
```

**Attach to Command:**

```
@app_commands.command(name="blackjack")
async def blackjack(self, interaction, bet):
    game_data = {'player_hand': [...], 'dealer_hand': [...]}
    view = BlackjackView(game_data, interaction.user.id, self.bot)
    await interaction.response.send_message(embed=..., view=view)
```

---

## 🧪 Testing

### **Local Testing**

1. **Setup test database:**
   ```
   createdb snipers_test
   psql -d snipers_test -f migrations/init.sql
   ```

2. **Use test bot token** (create separate bot in Discord portal)

3. **Run bot:**
   ```
   # Use test .env
   cp .env .env.prod
   cp .env.test .env
   python main.py
   ```

### **Unit Testing (TODO)**

Create `tests/` directory:

```
# tests/test_rng.py
import pytest
from utils.rng import ProvablyFairRNG

def test_rng_deterministic():
    rng = ProvablyFairRNG()
    result1 = rng.generate("test_seed")
    result2 = rng.generate("test_seed")
    assert result1 == result2  # Same seed = same result

def test_rng_range():
    rng = ProvablyFairRNG()
    result = rng.generate("test")
    assert 0.0 <= result <= 1.0
```

**Run tests:**
```
pip install pytest pytest-asyncio
pytest tests/
```

---

## 🚀 Deployment

### **Production Checklist**

- [ ] Set strong `CASINO_SERVER_SEED` in production (use `os.urandom(32).hex()`)
- [ ] Enable PostgreSQL connection pooling (min_size=5, max_size=20)
- [ ] Set `GUILD_ID` for instant command sync (or wait 1 hour for global)
- [ ] Enable Discord intents (SERVER MEMBERS, MESSAGE CONTENT)
- [ ] Use environment variables (never commit `.env` to Git)
- [ ] Setup database backups (pg_dump)
- [ ] Monitor logs (check for errors, failed transactions)
- [ ] Rate limit commands (discord.py has built-in cooldowns)

### **Environment Variables (Production)**

```
DISCORD_TOKEN=real_production_token
DATABASE_URL=postgresql://user:strongpass@prod-host:5432/snipers
GUILD_ID=123456789  # For instant sync
CASINO_REAL=1
LOAN_SYSTEM=0  # Disable if not ready
CASINO_SERVER_SEED=<64-char-hex>  # python -c "import os; print(os.urandom(32).hex())"
```

### **Docker Production**

```
# Dockerfile (multi-stage build)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser
CMD ["python", "main.py"]
```

---

## 📝 Code Style

### **Python Conventions**

- **PEP 8** compliance (use `black` formatter)
- **Type hints** where possible
- **Async/await** for all I/O operations
- **Docstrings** for public functions

### **Example:**

```
async def create_contract(
    self,
    conn: asyncpg.Connection,
    assigner_id: int,
    assignee_id: int,
    role: ContractRole,
    series: str,
    chapter: int,
    reward: int
) -> int:
    """
    Create a new contract in the database.
    
    Args:
        conn: Database connection
        assigner_id: User ID of contract creator
        assignee_id: User ID of assignee
        role: Contract role (RP, TL, etc.)
        series: Manga series name
        chapter: Chapter number
        reward: Reward amount in coins
    
    Returns:
        int: Newly created contract ID
    
    Raises:
        asyncpg.ForeignKeyViolationError: If user IDs don't exist
    """
    contract_id = await conn.fetchval("""
        INSERT INTO contracts (assigner_id, assignee_id, role, series, chapter, reward_amount)
        VALUES ($1, $2, $3::contract_role, $4, $5, $6)
        RETURNING id
    """, assigner_id, assignee_id, role.value, series, chapter, reward)
    return contract_id
```

---

## 🐛 Debugging

### **Enable Debug Logging**

```
# utils/logger.py
logger.setLevel(logging.DEBUG)  # Instead of INFO
```

### **Common Issues**

**1. Commands not showing in Discord:**
- Check `GUILD_ID` is set (instant sync) or wait 1 hour
- Verify bot has `applications.commands` scope
- Check console for "Commands synced" message

**2. Database deadlocks:**
- Always use `FOR UPDATE` when modifying user coins
- Keep transactions short (no external API calls inside)

**3. Button timeouts:**
- Buttons expire after 60 seconds (View timeout)
- Use persistent views for long-running interactions

### **Debugging Commands**

```
# Add debug command (admin only)
@app_commands.command(name="debug")
@app_commands.checks.has_permissions(administrator=True)
async def debug(self, interaction: discord.Interaction):
    info = f"""
    Bot Latency: {self.bot.latency * 1000:.0f}ms
    Guilds: {len(self.bot.guilds)}
    Loaded Cogs: {len(self.bot.cogs)}
    Database Pool: {self.bot.db.pool._holders.__len__()} connections
    """
    await interaction.response.send_message(f"```{info}```
```

---

## 📚 Resources

### **Documentation**

- [discord.py Docs](https://discordpy.readthedocs.io/en/stable/)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/current/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Discord API Docs](https://discord.com/developers/docs/intro)

### **Tutorials**

- [discord.py Cogs Tutorial](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)
- [asyncpg Transaction Safety](https://magicstack.github.io/asyncpg/current/usage.html#transactions)
- [Discord Slash Commands Guide](https://discordpy.readthedocs.io/en/stable/interactions/api.html)

---

## 🤝 Contributing Guidelines

1. **Fork the repo** and create a feature branch
2. **Write tests** for new features
3. **Update documentation** (README.md, DEVELOPMENT.md)
4. **Follow code style** (PEP 8, type hints, docstrings)
5. **Test thoroughly** (local + test server)
6. **Submit PR** with clear description

### **PR Template**

```
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Tested in production-like environment
- [ ] Added unit tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## 📧 Contact

- **GitHub Issues:** [Report bugs/features](https://github.com/pyhcho099/Snipers-bot/issues)
- **Email:** your-email@example.com
- **Discord:** Support server link

---

**Happy coding! 🚀**
```

***

## ✅ **What to Do Next**

1. **Copy both files** to your Snipers-bot repo root:
   - `README.md` - User-facing
   - `DEVELOPMENT.md` - Developer guide

2. **Customize:**
   - Replace `your-email@example.com` with real contact
   - Add Discord support server link
   - Add screenshots (optional)

3. **Commit and push:**
   ```bash
   git add README.md DEVELOPMENT.md
   git commit -m "docs: Add comprehensive documentation"
   git push origin main
   ```

Now your repo has **professional, complete documentation** that covers setup, usage, development, and deployment! 📚✨