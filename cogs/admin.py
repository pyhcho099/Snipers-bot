import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import create_success_embed, create_error_embed

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="addcoins", description="[ADMIN] Add coins to user")
    @app_commands.describe(user="Target user", amount="Amount to add")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcoins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO users (discord_id, codename) VALUES ($1, $2) ON CONFLICT DO NOTHING
                """, str(user.id), user.name)
                
                db_user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE", str(user.id))
                
                new_balance = db_user['coins'] + amount
                
                await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, db_user['id'])
                await conn.execute("""
                    INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                    VALUES ($1, $2, $3, $4, 'admin_adjustment')
                """, db_user['id'], 'earn' if amount > 0 else 'spend', abs(amount), new_balance)
        
        embed = create_success_embed("Coins Adjusted", f"**{amount}** coins → {user.mention}\nBalance: {new_balance}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="forcecomplete", description="[ADMIN] Force complete contract")
    @app_commands.describe(contract_id="Contract ID", reason="Reason")
    @app_commands.checks.has_permissions(administrator=True)
    async def forcecomplete(self, interaction: discord.Interaction, contract_id: int, reason: str):
        await interaction.response.defer()
        
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                contract = await conn.fetchrow("SELECT * FROM contracts WHERE id = $1 FOR UPDATE", contract_id)
                
                if not contract:
                    return await interaction.followup.send(embed=create_error_embed("Not Found", "Contract not found."))
                
                await conn.execute("UPDATE contracts SET status = 'completed', completed_at = NOW() WHERE id = $1", contract_id)
                
                assignee = await conn.fetchrow("SELECT id, coins FROM users WHERE id = $1 FOR UPDATE", contract['assignee_id'])
                new_balance = assignee['coins'] + contract['reward_amount']
                
                await conn.execute("""
                    UPDATE users SET coins = $1, contracts_completed = contracts_completed + 1 WHERE id = $2
                """, new_balance, assignee['id'])
                
                await conn.execute("""
                    INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
                    VALUES ($1, 'earn', $2, $3, 'force_complete', $4::jsonb)
                """, assignee['id'], contract['reward_amount'], new_balance, 
                     f'{{"contract_id": {contract_id}, "reason": "{reason}"}}')
        
        embed = create_success_embed(f"Contract #{contract_id} Force Completed", 
                                     f"Reason: {reason}\nReward: **{contract['reward_amount']}** coins")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
