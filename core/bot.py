import discord
from discord.ext import commands
from config import config
from core.database import db
from utils.logger import logger

class SnipersBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.db = db
        
    async def setup_hook(self):
        """Called when bot is starting up"""
        await self.db.create_pool()
        
        cogs = [
            'cogs.contracts',
            'cogs.bounties',
            'cogs.casino',
            'cogs.jokes',
            'cogs.loans',
            'cogs.rooms',
            'cogs.admin',
            'cogs.utility'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'✅ Loaded: {cog}')
            except Exception as e:
                logger.error(f'❌ Failed to load {cog}: {e}')
        
        try:
            if config.GUILD_ID:
                guild = discord.Object(id=config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f'✅ Commands synced to guild {config.GUILD_ID}')
            else:
                await self.tree.sync()
                logger.info('✅ Commands synced globally')
        except Exception as e:
            logger.error(f'❌ Failed to sync commands: {e}')
    
    async def on_ready(self):
        logger.info(f'🗡️  {self.user} is operational!')
        logger.info(f'📊 Serving {len(self.guilds)} guilds')
        logger.info(f'🎮 Casino: {"ON" if config.CASINO_REAL else "OFF"}')
        logger.info(f'💰 Loans: {"ON" if config.LOAN_SYSTEM else "OFF"}')
        
        await self.change_presence(
            activity=discord.Game(name="Snipers Operations | /help"),
            status=discord.Status.online
        )
    
    async def close(self):
        await self.db.close()
        await super().close()
