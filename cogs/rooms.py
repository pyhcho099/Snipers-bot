import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utils.embeds import create_success_embed, create_error_embed

class Rooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="room-create", description="Create a temporary private room")
    @app_commands.describe(name="Room name", duration_hours="Duration (1-168 hours)")
    async def room_create(self, interaction: discord.Interaction, name: str, duration_hours: int):
        await interaction.response.defer()
        
        if not (1 <= duration_hours <= 168):
            return await interaction.followup.send(embed=create_error_embed("Invalid", "Duration: 1-168 hours."))
        
        cost_per_hour = 10
        total_cost = cost_per_hour * duration_hours
        
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
                                              str(interaction.user.id))
                    
                    if not user or user['coins'] < total_cost:
                        return await interaction.followup.send(embed=create_error_embed("Insufficient", f"Need {total_cost} coins."))
                    
                    category = interaction.channel.category
                    overwrites = {
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                    
                    channel = await interaction.guild.create_text_channel(
                        name=name,
                        category=category,
                        overwrites=overwrites
                    )
                    
                    new_balance = user['coins'] - total_cost
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    
                    expires_at = datetime.now() + timedelta(hours=duration_hours)
                    room_id = await conn.fetchval("""
                        INSERT INTO rooms (discord_id, owner_id, name, cost_total, cost_per_user, expires_at)
                        VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
                    """, str(channel.id), user['id'], name, total_cost, cost_per_hour, expires_at)
                    
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
                        VALUES ($1, 'spend', $2, $3, 'room_creation', $4::jsonb)
                    """, user['id'], total_cost, new_balance, f'{{"room_id": {room_id}}}')
            
            embed = create_success_embed(
                f"Room #{room_id} Created",
                f"**Channel:** {channel.mention}\n**Cost:** {total_cost} coins\n**Expires:** <t:{int(expires_at.timestamp())}:R>"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Error", str(e)))

async def setup(bot):
    await bot.add_cog(Rooms(bot))
