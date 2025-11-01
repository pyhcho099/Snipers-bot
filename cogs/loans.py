import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import create_success_embed, create_error_embed
from config import config
from datetime import datetime, timedelta

class Loans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="loan-request", description="Request a loan")
    @app_commands.describe(amount="Loan amount (min 100)", days="Repayment days", interest="Interest % (0-10)")
    async def loan_request(self, interaction: discord.Interaction, amount: int, days: int, interest: int = 5):
        if not config.LOAN_SYSTEM:
            return await interaction.response.send_message("💰 Loans disabled.", ephemeral=True)
        
        if amount < 100:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 100 coins."))
        
        if not (1 <= days <= 30):
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Days: 1-30."))
        
        if not (0 <= interest <= 10):
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Interest: 0-10%."))
        
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (discord_id, codename) VALUES ($1, $2) ON CONFLICT DO NOTHING
            """, str(interaction.user.id), interaction.user.name)
            
            borrower = await conn.fetchrow("SELECT id FROM users WHERE discord_id = $1", str(interaction.user.id))
            
            due_date = datetime.now() + timedelta(days=days)
            
            loan_id = await conn.fetchval("""
                INSERT INTO loans (borrower_id, principal, interest_rate, due_at)
                VALUES ($1, $2, $3, $4) RETURNING id
            """, borrower['id'], amount, interest, due_date)
        
        embed = discord.Embed(
            title=f"💰 Loan Request #{loan_id}",
            description=f"**Amount:** {amount} coins\n**Interest:** {interest}%\n**Due:** <t:{int(due_date.timestamp())}:R>",
            color=0xffd700
        )
        embed.set_footer(text="Waiting for lender...")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Loans(bot))
