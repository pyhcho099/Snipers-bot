import discord
from discord import app_commands
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Show all commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🗡️ Snipers Bot Commands",
            description="Complete command reference",
            color=0x2f3136
        )
        
        embed.add_field(
            name="📜 Contracts",
            value="`/assign` - Assign contract\n`/submit` - Submit work\n`/balance` - Check stats",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Bounties",
            value="`/bounty-place` - Place bounty\n`/bounty-claim` - Claim bounty\n`/bounty-list` - List bounties\n`/bounty-resolve` - [ADMIN] Resolve",
            inline=False
        )
        
        embed.add_field(
            name="💬 Entertainment",
            value="`/joke` - Get joke\n`/uncensoredjoke` - Unfiltered\n`/multijoke` - Multiple jokes\n`/preferences` - Set preferences\n`/ratejoke` - Rating info",
            inline=False
        )
        
        embed.add_field(
            name="🎰 Casino",
            value="`/coinflip` `/blackjack` `/roulette`\n`/dice` `/crash` `/slots` `/lottery`",
            inline=False
        )
        
        embed.add_field(
            name="💰 Other",
            value="`/loan-request` - Request loan\n`/room-create` - Private room",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Admin",
            value="`/addcoins` - Add coins\n`/forcecomplete` - Force complete",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Utility",
            value="`/help` - This message\n`/ping` - Check latency",
            inline=False
        )
        
        embed.set_footer(text="Snipers Bot v4.0 | Python Edition")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency}ms**",
            color=0x5865f2
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
