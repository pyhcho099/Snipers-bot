#!/usr/bin/env python3
"""
Test script to verify Snipers Bot setup
"""

import sys
import os

print("🔍 Checking Snipers Bot Setup...\n")

# Check Python version
if sys.version_info < (3, 9):
    print("❌ Python 3.9+ required")
    sys.exit(1)
print("✅ Python version:", sys.version.split()[0])

# Check required files
required_files = [
    'main.py', 'config.py', 'requirements.txt',
    'core/bot.py', 'core/database.py',
    'migrations/init.sql'
]

missing = []
for f in required_files:
    if not os.path.exists(f):
        missing.append(f)
        print(f"❌ Missing: {f}")
    else:
        print(f"✅ Found: {f}")

# Check __init__.py files
init_folders = ['core', 'cogs', 'models', 'utils', 'services']
for folder in init_folders:
    init_file = f"{folder}/__init__.py"
    if not os.path.exists(init_file):
        missing.append(init_file)
        print(f"❌ Missing: {init_file}")
    else:
        print(f"✅ Found: {init_file}")

# Check .env file
if not os.path.exists('.env'):
    print("⚠️  .env file not found - copy from .env.example")
else:
    print("✅ .env file exists")

# Try importing
print("\n📦 Testing imports...")
try:
    from config import config
    print("✅ config imports correctly")
except Exception as e:
    print(f"❌ config import failed: {e}")

try:
    import discord
    print(f"✅ discord.py version: {discord.__version__}")
except:
    print("❌ discord.py not installed - run: pip install -r requirements.txt")

try:
    import asyncpg
    print("✅ asyncpg installed")
except:
    print("❌ asyncpg not installed")

if missing:
    print(f"\n❌ {len(missing)} files missing!")
    sys.exit(1)
else:
    print("\n✅ All files present! Ready to run.")
