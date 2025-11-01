import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View
import aiohttp

class JokePreferenceView(View):
    def __init__(self, user_id, bot):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bot = bot
        
        select = Select(
            placeholder="Choose your joke preference...",
            options=[
                discord.SelectOption(label="Safe Mode", value="safe", emoji="✅", description="Family-friendly jokes"),
                discord.SelectOption(label="Uncensored", value="uncensored", emoji="⚠️", description="All jokes including mature")
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Not your menu!", ephemeral=True)
        
        mode = interaction.data['values'][0]
        
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_preferences (user_id, joke_mode)
                VALUES ((SELECT id FROM users WHERE discord_id = $1), $2)
                ON CONFLICT (user_id) DO UPDATE SET joke_mode = $2, updated_at = NOW()
            """, str(self.user_id), mode)
        
        embed = discord.Embed(title="✅ Preference Updated", description=f"Joke mode: **{mode.upper()}**", color=0x57f287)
        await interaction.response.edit_message(embed=embed, view=None)


class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://v2.jokeapi.dev/joke"
    
    async def get_user_preference(self, user_id: str):
        async with self.bot.db.acquire() as conn:
            pref = await conn.fetchrow("""
                SELECT joke_mode FROM user_preferences 
                WHERE user_id = (SELECT id FROM users WHERE discord_id = $1)
            """, user_id)
            return pref['joke_mode'] if pref else 'safe'
    
    async def fetch_joke(self, category: str, safe_mode: bool):
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base}/{category}"
            if safe_mode:
                url += "?safe-mode"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    
    @app_commands.command(name="joke", description="Get a joke (respects your preference)")
    @app_commands.describe(category="Joke category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Programming", value="Programming"),
        app_commands.Choice(name="Misc", value="Misc"),
        app_commands.Choice(name="Pun", value="Pun"),
        app_commands.Choice(name="Spooky", value="Spooky"),
        app_commands.Choice(name="Christmas", value="Christmas"),
        app_commands.Choice(name="Any", value="Any")
    ])
    async def joke(self, interaction: discord.Interaction, category: str = "Any"):
        await interaction.response.defer()
        
        pref = await self.get_user_preference(str(interaction.user.id))
        safe_mode = (pref == 'safe')
        
        data = await self.fetch_joke(category, safe_mode)
        
        if not data or data.get('error'):
            return await interaction.followup.send("😅 Couldn't fetch a joke!")
        
        embed = discord.Embed(title="🎭 Here's a Joke!", color=0xffea00)
        embed.add_field(name="Category", value=data['category'], inline=False)
        
        if data['type'] == 'single':
            embed.add_field(name="Joke", value=data['joke'], inline=False)
        else:
            embed.add_field(name="Setup", value=data['setup'], inline=False)
            embed.add_field(name="Delivery", value=data['delivery'], inline=False)
        
        embed.set_footer(text=f"Source: JokeAPI | Mode: {pref.upper()}")
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction("😂")
        await message.add_reaction("😐")
        await message.add_reaction("😔")
    
    @app_commands.command(name="uncensoredjoke", description="Get an unfiltered joke")
    @app_commands.describe(category="Joke category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Programming", value="Programming"),
        app_commands.Choice(name="Misc", value="Misc"),
        app_commands.Choice(name="Dark", value="Dark"),
        app_commands.Choice(name="Pun", value="Pun"),
        app_commands.Choice(name="Any", value="Any")
    ])
    async def uncensored_joke(self, interaction: discord.Interaction, category: str = "Any"):
        await interaction.response.defer()
        
        is_nsfw = getattr(interaction.channel, 'nsfw', False)
        
        data = await self.fetch_joke(category, safe_mode=False)
        
        if not data or data.get('error'):
            return await interaction.followup.send("😅 Couldn't get a joke.")
        
        flags = data.get('flags', {})
        if flags.get('nsfw') and not is_nsfw:
            return await interaction.followup.send("This joke's too wild for here 👀")
        
        embed = discord.Embed(title="⚠️ Uncensored Humor!", color=0xff0000)
        embed.add_field(name="Category", value=data['category'], inline=False)
        
        if data['type'] == 'single':
            embed.add_field(name="Joke", value=data['joke'], inline=False)
        else:
            embed.add_field(name="Setup", value=data['setup'], inline=False)
            embed.add_field(name="Delivery", value=data['delivery'], inline=False)
        
        embed.set_footer(text="Source: JokeAPI (Uncensored)")
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction("😂")
        await message.add_reaction("😐")
        await message.add_reaction("😔")
    
    @app_commands.command(name="multijoke", description="Get multiple jokes at once")
    @app_commands.describe(count="Number of jokes (1-5)", category="Joke category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Programming", value="Programming"),
        app_commands.Choice(name="Misc", value="Misc"),
        app_commands.Choice(name="Any", value="Any")
    ])
    async def multijoke(self, interaction: discord.Interaction, count: int = 3, category: str = "Any"):
        await interaction.response.defer()
        
        if not (1 <= count <= 5):
            return await interaction.followup.send("Choose 1-5 jokes.")
        
        pref = await self.get_user_preference(str(interaction.user.id))
        safe_mode = (pref == 'safe')
        
        jokes = []
        for _ in range(count):
            data = await self.fetch_joke(category, safe_mode)
            if data and not data.get('error'):
                if data['type'] == 'single':
                    jokes.append(data['joke'])
                else:
                    jokes.append(f"{data['setup']}\n→ {data['delivery']}")
        
        if not jokes:
            return await interaction.followup.send("😅 Couldn't fetch jokes!")
        
        embed = discord.Embed(title=f"🎭 Here are {len(jokes)} Jokes!", color=0xffea00)
        
        for i, joke in enumerate(jokes, 1):
            embed.add_field(name=f"Joke #{i}", value=joke[:1024], inline=False)
        
        embed.set_footer(text=f"Source: JokeAPI | Mode: {pref.upper()}")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="preferences", description="Set your joke preferences")
    async def preferences(self, interaction: discord.Interaction):
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (discord_id, codename) VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, str(interaction.user.id), interaction.user.name)
        
        embed = discord.Embed(
            title="🎭 Joke Preferences",
            description="Choose your default joke mode:",
            color=0x5865f2
        )
        
        view = JokePreferenceView(interaction.user.id, self.bot)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="ratejoke", description="View joke rating info")
    async def ratejoke(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="😂 Joke Rating System",
            description="React to jokes with:\n😂 - Hilarious\n😐 - Okay\n😔 - Not funny\n\nRatings help improve quality!",
            color=0xffea00
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Jokes(bot))
