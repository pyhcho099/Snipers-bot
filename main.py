import asyncio
from core.bot import SnipersBot
from config import config
from utils.logger import logger

async def main():
    bot = SnipersBot()
    
    try:
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not set in .env file!")
        exit(1)
    
    asyncio.run(main())
