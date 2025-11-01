import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import create_success_embed, create_error_embed
from datetime import datetime, timedelta

class Bounties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="bounty-place", description="Place a bounty on a user")
    @app_commands.describe(target="Target user", amount="Bounty amount (min 100)", reason="Reason")
    async def bounty_place(self, interaction: discord.Interaction, target: discord.Member, amount: int, reason: str):
        await interaction.response.defer()
        
        if amount < 100:
            await interaction.followup.send(embed=create_error_embed("Invalid", "Min bounty: 100 coins."))
            return
        
        if target.id == interaction.user.id:
            await interaction.followup.send(embed=create_error_embed("Invalid", "Can't bounty yourself!"))
            return
        
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    placer = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
                                                str(interaction.user.id))
                    
                    if not placer or placer['coins'] < amount:
                        await interaction.followup.send(embed=create_error_embed("Insufficient", f"Need {amount} coins."))
                        return
                    
                    await conn.execute("INSERT INTO users (discord_id, codename) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                                     str(target.id), target.name)
                    
                    new_balance = placer['coins'] - amount
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, placer['id'])
                    
                    bounty_id = await conn.fetchval("""
                        INSERT INTO bounties (target_id, placed_by_id, amount, reason, expires_at)
                        VALUES ((SELECT id FROM users WHERE discord_id = $1), $2, $3, $4, $5) RETURNING id
                    """, str(target.id), placer['id'], amount, reason, datetime.now() + timedelta(days=7))
                    
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
                        VALUES ($1, 'spend', $2, $3, 'bounty_placement', $4::jsonb)
                    """, placer['id'], amount, new_balance, f'{{"bounty_id": {bounty_id}}}')
            
            embed = discord.Embed(
                title=f"🎯 Bounty #{bounty_id} Placed",
                description=f"**Target:** {target.mention}\n**Amount:** {amount} coins\n**Reason:** {reason}",
                color=0xff0000
            )
            embed.set_footer(text="Expires in 7 days")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))
    
    @app_commands.command(name="bounty-claim", description="Claim a bounty with evidence")
    @app_commands.describe(bounty_id="Bounty ID", evidence="Evidence URL")
    async def bounty_claim(self, interaction: discord.Interaction, bounty_id: int, evidence: str):
        await interaction.response.defer()
        
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    bounty = await conn.fetchrow("SELECT * FROM bounties WHERE id = $1 FOR UPDATE", bounty_id)
                    
                    if not bounty or bounty['status'] != 'open':
                        await interaction.followup.send(embed=create_error_embed("Invalid", "Bounty not available."))
                        return
                    
                    await conn.execute("INSERT INTO users (discord_id, codename) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                                     str(interaction.user.id), interaction.user.name)
                    
                    await conn.execute("""
                        UPDATE bounties SET status = 'claimed'::bounty_status, 
                        claim_proof = $1, claimant_id = (SELECT id FROM users WHERE discord_id = $2)
                        WHERE id = $3
                    """, evidence, str(interaction.user.id), bounty_id)
            
            embed = create_success_embed(f"Bounty #{bounty_id} Claimed", "Under review by admins.")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))
    
    @app_commands.command(name="bounty-list", description="List all open bounties")
    async def bounty_list(self, interaction: discord.Interaction):
        async with self.bot.db.acquire() as conn:
            bounties = await conn.fetch("""
                SELECT b.id, b.amount, b.reason, u.discord_id
                FROM bounties b JOIN users u ON b.target_id = u.id
                WHERE b.status = 'open' ORDER BY b.amount DESC LIMIT 10
            """)
        
        if not bounties:
            await interaction.response.send_message("No open bounties.")
            return
        
        embed = discord.Embed(title="🎯 Open Bounties", color=0xff0000)
        
        for b in bounties:
            try:
                target = await self.bot.fetch_user(int(b['discord_id']))
                embed.add_field(
                    name=f"Bounty #{b['id']} - {b['amount']} coins",
                    value=f"**Target:** {target.mention}\n**Reason:** {b['reason'][:50]}...",
                    inline=False
                )
            except:
                pass
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="bounty-resolve", description="[ADMIN] Resolve a bounty claim")
    @app_commands.describe(bounty_id="Bounty ID", verdict="approve or reject")
    @app_commands.choices(verdict=[
        app_commands.Choice(name="Approve", value="approve"),
        app_commands.Choice(name="Reject", value="reject")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def bounty_resolve(self, interaction: discord.Interaction, bounty_id: int, verdict: str):
        await interaction.response.defer()
        
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    bounty = await conn.fetchrow("SELECT * FROM bounties WHERE id = $1 FOR UPDATE", bounty_id)
                    
                    if not bounty or bounty['status'] != 'claimed':
                        await interaction.followup.send(embed=create_error_embed("Invalid", "Bounty not claimed."))
                        return
                    
                    if verdict == "approve":
                        claimant = await conn.fetchrow("SELECT id, coins FROM users WHERE id = $1 FOR UPDATE",
                                                      bounty['claimant_id'])
                        new_balance = claimant['coins'] + bounty['amount']
                        
                        await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, claimant['id'])
                        await conn.execute("UPDATE bounties SET status = 'resolved'::bounty_status WHERE id = $1", bounty_id)
                        await conn.execute("""
                            INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
                            VALUES ($1, 'earn', $2, $3, 'bounty_reward', $4::jsonb)
                        """, claimant['id'], bounty['amount'], new_balance, f'{{"bounty_id": {bounty_id}}}')
                        
                        msg = f"Approved! **+{bounty['amount']} coins** to claimant."
                    else:
                        await conn.execute("UPDATE bounties SET status = 'open'::bounty_status, claimant_id = NULL WHERE id = $1",
                                         bounty_id)
                        msg = "Rejected. Bounty reopened."
            
            embed = create_success_embed(f"Bounty #{bounty_id} Resolved", msg)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))

async def setup(bot):
    await bot.add_cog(Bounties(bot))
