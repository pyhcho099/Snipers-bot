import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.embeds import create_success_embed, create_error_embed

class Contracts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="assign", description="Assign a contract to a user")
    @app_commands.describe(
        user="The user to assign",
        role="Contract role",
        series="Series name",
        chapter="Chapter number",
        reward="Reward in coins",
        deadline="Optional deadline (ISO format)"
    )
    @app_commands.choices(role=[
        app_commands.Choice(name="RP", value="rp"),
        app_commands.Choice(name="TL", value="tl"),
        app_commands.Choice(name="PR", value="pr"),
        app_commands.Choice(name="CLRD", value="clrd"),
        app_commands.Choice(name="TS", value="ts"),
        app_commands.Choice(name="QC", value="qc"),
        app_commands.Choice(name="Uploader", value="uploader")
    ])
    async def assign(self, interaction: discord.Interaction, user: discord.Member,
                     role: str, series: str, chapter: int, reward: int, deadline: str = None):
        await interaction.response.defer()
        
        if reward < 0:
            await interaction.followup.send(embed=create_error_embed("Invalid", "Reward must be positive."))
            return
        
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (discord_id, codename) 
                    VALUES ($1, $2), ($3, $4)
                    ON CONFLICT (discord_id) DO UPDATE SET last_seen = NOW()
                """, str(interaction.user.id), interaction.user.name, str(user.id), user.name)
                
                contract_id = await conn.fetchval("""
                    INSERT INTO contracts 
                    (assigner_id, assignee_id, role, series, chapter, reward_amount, due_at)
                    VALUES (
                        (SELECT id FROM users WHERE discord_id = $1),
                        (SELECT id FROM users WHERE discord_id = $2),
                        $3::contract_role, $4, $5, $6, $7::timestamptz
                    ) RETURNING id
                """, str(interaction.user.id), str(user.id), role, series, chapter, reward, deadline)
            
            deadline_text = None
            if deadline:
                try:
                    dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    deadline_text = f"<t:{int(dt.timestamp())}:R>"
                except:
                    pass
            
            embed = discord.Embed(
                title=f"🗡️ Contract #{contract_id} Assigned",
                description=f"**Role:** {role.upper()}\n**Series:** {series} ch.{chapter}\n**Reward:** {reward} coins",
                color=0x2f3136
            )
            if deadline_text:
                embed.add_field(name="Deadline", value=deadline_text)
            
            await interaction.followup.send(embed=embed)
            
            try:
                await user.send(f"📜 New contract: **{role.upper()}** for *{series}* ch.{chapter}")
            except:
                pass
                
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))
    
    @app_commands.command(name="submit", description="Submit completed work")
    @app_commands.describe(contract_id="Contract ID", proof="Proof URL", notes="Optional notes")
    async def submit(self, interaction: discord.Interaction, contract_id: int, proof: str, notes: str = None):
        await interaction.response.defer()
        
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    contract = await conn.fetchrow("""
                        SELECT c.*, u.discord_id as assignee_discord_id
                        FROM contracts c
                        JOIN users u ON c.assignee_id = u.id
                        WHERE c.id = $1 FOR UPDATE
                    """, contract_id)
                    
                    if not contract:
                        await interaction.followup.send(embed=create_error_embed("Not Found", "Contract not found."))
                        return
                    
                    if contract['status'] != 'active':
                        await interaction.followup.send(embed=create_error_embed("Invalid", "Contract not active."))
                        return
                    
                    submitter = await conn.fetchrow("SELECT id FROM users WHERE discord_id = $1", str(interaction.user.id))
                    is_assignee = contract['assignee_discord_id'] == str(interaction.user.id)
                    is_admin = interaction.user.guild_permissions.administrator
                    
                    if not (is_assignee or is_admin):
                        await interaction.followup.send(embed=create_error_embed("Permission Denied", "Can't submit."))
                        return
                    
                    await conn.execute("""
                        INSERT INTO contract_submissions (contract_id, submitter_id, proof_url, notes)
                        VALUES ($1, $2, $3, $4)
                    """, contract_id, submitter['id'], proof, notes)
                    
                    await conn.execute("""
                        UPDATE contracts SET status = 'completed', proof_url = $1, completed_at = NOW()
                        WHERE id = $2
                    """, proof, contract_id)
                    
                    assignee = await conn.fetchrow("SELECT id, coins FROM users WHERE id = $1 FOR UPDATE", contract['assignee_id'])
                    new_balance = assignee['coins'] + contract['reward_amount']
                    
                    await conn.execute("UPDATE users SET coins = $1, contracts_completed = contracts_completed + 1 WHERE id = $2", 
                                     new_balance, assignee['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
                        VALUES ($1, 'earn', $2, $3, 'contract_reward', $4::jsonb)
                    """, assignee['id'], contract['reward_amount'], new_balance, f'{{"contract_id": {contract_id}}}')
            
            embed = create_success_embed(f"Contract #{contract_id} Complete", 
                                        f"**+{contract['reward_amount']} coins**")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))
    
    @app_commands.command(name="balance", description="Check your balance")
    async def balance(self, interaction: discord.Interaction):
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT coins, xp, rank, contracts_completed FROM users WHERE discord_id = $1", 
                                      str(interaction.user.id))
            
            if not user:
                await conn.execute("INSERT INTO users (discord_id, codename) VALUES ($1, $2)",
                                 str(interaction.user.id), interaction.user.name)
                user = {'coins': 0, 'xp': 0, 'rank': 'Recruit', 'contracts_completed': 0}
        
        embed = discord.Embed(title=f"💰 {interaction.user.name}'s Profile", color=0xffd700)
        embed.add_field(name="Coins", value=f"{user['coins']:,}", inline=True)
        embed.add_field(name="Rank", value=user['rank'], inline=True)
        embed.add_field(name="Contracts", value=user['contracts_completed'], inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Contracts(bot))
