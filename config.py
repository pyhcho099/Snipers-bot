import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    GUILD_ID = int(os.getenv('GUILD_ID', 0)) if os.getenv('GUILD_ID') else None
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Feature Flags
    CASINO_REAL = os.getenv('CASINO_REAL', '1') == '1'
    LOAN_SYSTEM = os.getenv('LOAN_SYSTEM', '0') == '1'
    AI_WEBHOOKS = os.getenv('AI_WEBHOOKS', '0') == '1'
    
    # Casino
    CASINO_SERVER_SEED = os.getenv('CASINO_SERVER_SEED', os.urandom(32).hex())

config = Config()
