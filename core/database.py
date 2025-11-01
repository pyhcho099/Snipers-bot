import asyncpg
from contextlib import asynccontextmanager
from config import config
from utils.logger import logger

class Database:
    def __init__(self):
        self.pool = None
    
    async def create_pool(self):
        """Initialize asyncpg connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=config.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Database pool created")
            
            # Run migrations
            try:
                async with self.pool.acquire() as conn:
                    with open('migrations/init.sql', 'r') as f:
                        await conn.execute(f.read())
                logger.info("✅ Database migrations applied")
            except FileNotFoundError:
                logger.warning("⚠️  migrations/init.sql not found - skipping")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as connection:
            yield connection
    
    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

db = Database()
