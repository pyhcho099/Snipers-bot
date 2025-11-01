#!/usr/bin/env python3
"""
Snipers Bot - Complete Setup Verification Script
Run this in your repo root to check if everything is ready
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("ðŸ—¡ï¸  SNIPERS BOT - SETUP VERIFICATION")
print("=" * 80)
print()

# Color codes for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check(condition, message):
    if condition:
        print(f"{Colors.GREEN}âœ… {message}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}âŒ {message}{Colors.END}")
        return False

def warn(message):
    print(f"{Colors.YELLOW}âš ï¸  {message}{Colors.END}")

# Track issues
issues = []
warnings = []

print("ðŸ“‹ STEP 1: Checking Python Version")
print("-" * 80)
version_ok = check(sys.version_info >= (3, 9), f"Python 3.9+ (Current: {sys.version.split()[0]})")
if not version_ok:
    issues.append("Python version too old")
print()

print("ðŸ“ STEP 2: Checking File Structure")
print("-" * 80)

required_files = {
    "Root": [
        "main.py",
        "config.py", 
        "requirements.txt",
        ".env.example",
        "README.md"
    ],
    "core/": [
        "__init__.py",
        "bot.py",
        "database.py"
    ],
    "cogs/": [
        "__init__.py",
        "contracts.py",
        "bounties.py",
        "casino.py",
        "jokes.py",
        "loans.py",
        "rooms.py",
        "admin.py",
        "utility.py"
    ],
    "models/": [
        "__init__.py",
        "enums.py",
        "user.py",
        "contract.py"
    ],
    "utils/": [
        "__init__.py",
        "logger.py",
        "rng.py",
        "embeds.py"
    ],
    "services/": [
        "__init__.py",
        "png_service.py",
        "transaction_service.py"
    ],
    "migrations/": [
        "init.sql"
    ]
}

total_files = 0
found_files = 0
missing_files = []

for folder, files in required_files.items():
    print(f"\n  ðŸ“‚ {folder}")
    for filename in files:
        total_files += 1
        if folder == "Root":
            filepath = filename
        else:
            filepath = os.path.join(folder, filename)

        exists = os.path.exists(filepath)
        if exists:
            found_files += 1
            # Check if file is empty
            size = os.path.getsize(filepath)
            if size == 0 and filename != "__init__.py":
                warn(f"     {filename} exists but is EMPTY (0 bytes)")
                warnings.append(f"{filepath} is empty")
            else:
                print(f"{Colors.GREEN}     âœ“ {filename}{Colors.END}")
        else:
            print(f"{Colors.RED}     âœ— {filename} MISSING{Colors.END}")
            missing_files.append(filepath)
            issues.append(f"Missing file: {filepath}")

print()
print(f"Files found: {found_files}/{total_files}")
print()

print("ðŸ“¦ STEP 3: Checking Dependencies")
print("-" * 80)

try:
    import discord
    check(True, f"discord.py installed (v{discord.__version__})")
except ImportError:
    check(False, "discord.py NOT installed")
    issues.append("discord.py not installed")

try:
    import asyncpg
    check(True, "asyncpg installed")
except ImportError:
    check(False, "asyncpg NOT installed")
    issues.append("asyncpg not installed")

try:
    import aiohttp
    check(True, "aiohttp installed")
except ImportError:
    check(False, "aiohttp NOT installed")
    issues.append("aiohttp not installed")

try:
    from PIL import Image
    check(True, "Pillow installed")
except ImportError:
    check(False, "Pillow NOT installed")
    issues.append("Pillow not installed")

try:
    import pydantic
    check(True, "pydantic installed")
except ImportError:
    check(False, "pydantic NOT installed")
    issues.append("pydantic not installed")

print()

print("âš™ï¸  STEP 4: Checking Configuration")
print("-" * 80)

env_exists = os.path.exists('.env')
if env_exists:
    check(True, ".env file exists")

    # Read and check required vars
    with open('.env', 'r') as f:
        env_content = f.read()

    required_vars = ['DISCORD_TOKEN', 'DATABASE_URL', 'GUILD_ID']
    for var in required_vars:
        if var in env_content:
            # Check if it's not just a placeholder
            if 'your_' in env_content or 'changeme' in env_content:
                warn(f"{var} found but may be placeholder")
                warnings.append(f"{var} might be placeholder value")
            else:
                check(True, f"{var} is set")
        else:
            check(False, f"{var} NOT found in .env")
            issues.append(f"Missing {var} in .env")
else:
    check(False, ".env file NOT found (copy from .env.example)")
    issues.append("No .env file")

print()

print("ðŸ” STEP 5: Checking Code Syntax")
print("-" * 80)

# Check main.py can be imported
if os.path.exists('main.py'):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "main.py")
        if spec and spec.loader:
            check(True, "main.py syntax is valid")
        else:
            check(False, "main.py has syntax errors")
            issues.append("main.py syntax error")
    except Exception as e:
        check(False, f"main.py import failed: {str(e)[:50]}")
        issues.append(f"main.py import error: {e}")
else:
    check(False, "main.py not found")

# Check config.py
if os.path.exists('config.py'):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", "config.py")
        if spec and spec.loader:
            check(True, "config.py syntax is valid")
        else:
            check(False, "config.py has syntax errors")
            issues.append("config.py syntax error")
    except Exception as e:
        check(False, f"config.py import failed: {str(e)[:50]}")
        issues.append(f"config.py import error: {e}")

print()

print("ðŸ—„ï¸  STEP 6: Checking Database Schema")
print("-" * 80)

if os.path.exists('migrations/init.sql'):
    with open('migrations/init.sql', 'r') as f:
        sql_content = f.read()

    required_tables = ['users', 'contracts', 'bounties', 'loans', 'transactions', 'rooms', 'logs', 'user_preferences']
    for table in required_tables:
        if f"CREATE TABLE" in sql_content and table in sql_content:
            check(True, f"Table '{table}' defined")
        else:
            check(False, f"Table '{table}' NOT defined")
            issues.append(f"Missing table: {table}")

    # Check for enums
    required_enums = ['contract_role', 'txn_type', 'bounty_status', 'loan_status']
    for enum in required_enums:
        if f"CREATE TYPE {enum}" in sql_content:
            check(True, f"Enum '{enum}' defined")
        else:
            check(False, f"Enum '{enum}' NOT defined")
            issues.append(f"Missing enum: {enum}")
else:
    check(False, "migrations/init.sql NOT found")
    issues.append("No database schema file")

print()

print("=" * 80)
print("ðŸ“Š SUMMARY")
print("=" * 80)

if not issues and not warnings:
    print(f"{Colors.GREEN}")
    print("âœ… ALL CHECKS PASSED!")
    print("Your Snipers Bot is ready to run!")
    print(f"{Colors.END}")
    print()
    print("Next steps:")
    print("1. Make sure PostgreSQL is running")
    print("2. Create database: createdb snipers")
    print("3. Run bot: python main.py")
elif not issues:
    print(f"{Colors.YELLOW}")
    print(f"âš ï¸  {len(warnings)} WARNINGS but no critical issues")
    print("Bot should work but review warnings above")
    print(f"{Colors.END}")
else:
    print(f"{Colors.RED}")
    print(f"âŒ FOUND {len(issues)} CRITICAL ISSUES")
    print(f"{Colors.END}")
    print()
    print("Critical Issues:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    if warnings:
        print()
        print("Warnings:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    print()
    print("Fix these issues before running the bot!")

print()

if missing_files:
    print("=" * 80)
    print("ðŸ”§ QUICK FIX COMMANDS")
    print("=" * 80)
    print()
    print("Create missing files with these commands:")
    print()

    # Group by directory
    dirs_needed = set()
    for f in missing_files:
        if '/' in f:
            dirs_needed.add(f.split('/')[0])

    if dirs_needed:
        print("# Create missing directories:")
        for d in sorted(dirs_needed):
            print(f"mkdir -p {d}")
        print()

    print("# Create missing __init__.py files:")
    for f in missing_files:
        if '__init__.py' in f:
            print(f"touch {f}")
    print()

    print("# Install dependencies:")
    print("pip install -r requirements.txt")
    print()

print("=" * 80)
sys.exit(0 if not issues else 1)