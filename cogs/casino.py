import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from utils.rng import rng
from utils.embeds import create_error_embed, create_success_embed
from config import config
import random
import asyncio

class BlackjackView(View):
    def __init__(self, game_data, user_id, bot):
        super().__init__(timeout=60)
        self.game_data = game_data
        self.user_id = user_id
        self.bot = bot
        self.finished = False
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id or self.finished:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
        
        card = random.randint(1, 11)
        self.game_data['player_hand'].append(card)
        player_total = sum(self.game_data['player_hand'])
        
        if player_total > 21:
            await self.end_game(interaction, False, "Bust!")
        elif player_total == 21:
            await self.end_game(interaction, True, "Blackjack!")
        else:
            embed = discord.Embed(
                title="🎴 Blackjack",
                description=f"**Your hand:** {self.game_data['player_hand']} = **{player_total}**\n**Dealer:** {self.game_data['dealer_hand'][0]}, ?",
                color=0x5865f2
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id or self.finished:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
        
        dealer_total = sum(self.game_data['dealer_hand'])
        while dealer_total < 17:
            self.game_data['dealer_hand'].append(random.randint(1, 11))
            dealer_total = sum(self.game_data['dealer_hand'])
        
        player_total = sum(self.game_data['player_hand'])
        
        if dealer_total > 21 or player_total > dealer_total:
            await self.end_game(interaction, True, f"Win! Dealer: {dealer_total}, You: {player_total}")
        elif dealer_total > player_total:
            await self.end_game(interaction, False, f"Loss! Dealer: {dealer_total}, You: {player_total}")
        else:
            await self.end_game(interaction, None, f"Push! Both: {player_total}")
    
    async def end_game(self, interaction, won, message):
        self.finished = True
        bet = self.game_data['bet']
        
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
                                         str(self.user_id))
                
                if won is True:
                    new_balance = user['coins'] + bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'blackjack_win')
                    """, user['id'], bet, new_balance)
                    embed = create_success_embed("🎉 Blackjack Win!", f"{message}\n\n**+{bet} coins**\nBalance: {new_balance}")
                elif won is False:
                    new_balance = user['coins'] - bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'blackjack_loss')
                    """, user['id'], bet, new_balance)
                    embed = discord.Embed(title="💔 Loss", description=f"{message}\n\n**-{bet} coins**\nBalance: {new_balance}", color=0xed4245)
                else:
                    embed = discord.Embed(title="🤝 Push", description=f"{message}\n\nBet returned.", color=0xffea00)
        
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class CrashView(View):
    def __init__(self, crash_point, bet, user_id, bot):
        super().__init__(timeout=30)
        self.crash_point = crash_point
        self.bet = bet
        self.user_id = user_id
        self.bot = bot
        self.multiplier = 1.0
        self.cashed_out = False
    
    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.success)
    async def cashout_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id or self.cashed_out:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
        
        self.cashed_out = True
        winnings = int(self.bet * self.multiplier)
        
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1 FOR UPDATE",
                                         str(self.user_id))
                new_balance = user['coins'] + winnings
                await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                await conn.execute("""
                    INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                    VALUES ($1, 'earn', $2, $3, 'crash_win')
                """, user['id'], winnings, new_balance)
        
        embed = create_success_embed("💰 Cashed Out!", f"**{self.multiplier:.2f}x**\n**+{winnings} coins**\nBalance: {new_balance}")
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="coinflip", description="Flip a coin")
    @app_commands.describe(bet="Amount to bet")
    async def coinflip(self, interaction: discord.Interaction, bet: int):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 1:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 1 coin."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
            
            result = rng.generate(str(interaction.user.id))
            win = result >= 0.5
            
            async with conn.transaction():
                if win:
                    new_balance = user['coins'] + bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'coinflip_win')
                    """, user['id'], bet, new_balance)
                    embed = create_success_embed("🎉 Won!", f"**HEADS**\n\n**+{bet} coins**\nBalance: {new_balance}")
                else:
                    new_balance = user['coins'] - bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'coinflip_loss')
                    """, user['id'], bet, new_balance)
                    embed = discord.Embed(title="💔 Lost", description=f"**TAILS**\n\n**-{bet} coins**\nBalance: {new_balance}", color=0xed4245)
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="blackjack", description="Play blackjack")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 10:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 10 coins."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
        
        player_hand = [random.randint(1, 11), random.randint(1, 11)]
        dealer_hand = [random.randint(1, 11), random.randint(1, 11)]
        
        game_data = {'player_hand': player_hand, 'dealer_hand': dealer_hand, 'bet': bet}
        
        embed = discord.Embed(
            title="🎴 Blackjack",
            description=f"**Your hand:** {player_hand} = **{sum(player_hand)}**\n**Dealer:** {dealer_hand[0]}, ?",
            color=0x5865f2
        )
        
        view = BlackjackView(game_data, interaction.user.id, self.bot)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="roulette", description="Bet on roulette")
    @app_commands.describe(bet="Amount", choice="red, black, green, or 0-36")
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: str):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 1:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 1 coin."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
            
            number = random.randint(0, 36)
            
            if number == 0:
                color = 'green'
            elif number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                color = 'red'
            else:
                color = 'black'
            
            win = False
            multiplier = 0
            
            if choice.lower() in ['red', 'black', 'green']:
                if choice.lower() == color:
                    win = True
                    multiplier = 14 if color == 'green' else 2
            elif choice.isdigit() and 0 <= int(choice) <= 36:
                if int(choice) == number:
                    win = True
                    multiplier = 35
            
            async with conn.transaction():
                if win:
                    winnings = bet * multiplier
                    new_balance = user['coins'] + winnings
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'roulette_win')
                    """, user['id'], winnings, new_balance)
                    embed = create_success_embed("🎉 Roulette Win!", 
                                                f"**{number} {color.upper()}**\n**+{winnings} coins** ({multiplier}x)\nBalance: {new_balance}")
                else:
                    new_balance = user['coins'] - bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'roulette_loss')
                    """, user['id'], bet, new_balance)
                    embed = discord.Embed(title="💔 Loss", 
                                        description=f"**{number} {color.upper()}**\n**-{bet} coins**\nBalance: {new_balance}", 
                                        color=0xed4245)
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="dice", description="Roll dice")
    @app_commands.describe(bet="Amount", prediction="over7, under7, or seven")
    @app_commands.choices(prediction=[
        app_commands.Choice(name="Over 7", value="over7"),
        app_commands.Choice(name="Under 7", value="under7"),
        app_commands.Choice(name="Exactly 7", value="seven")
    ])
    async def dice(self, interaction: discord.Interaction, bet: int, prediction: str):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 1:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 1 coin."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
            
            dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
            total = dice1 + dice2
            
            win = False
            multiplier = 0
            
            if prediction == "over7" and total > 7:
                win, multiplier = True, 2
            elif prediction == "under7" and total < 7:
                win, multiplier = True, 2
            elif prediction == "seven" and total == 7:
                win, multiplier = True, 4
            
            async with conn.transaction():
                if win:
                    winnings = bet * multiplier
                    new_balance = user['coins'] + winnings
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'dice_win')
                    """, user['id'], winnings, new_balance)
                    embed = create_success_embed("🎲 Dice Win!", 
                                                f"**{dice1} + {dice2} = {total}**\n**+{winnings} coins** ({multiplier}x)\nBalance: {new_balance}")
                else:
                    new_balance = user['coins'] - bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'dice_loss')
                    """, user['id'], bet, new_balance)
                    embed = discord.Embed(title="🎲 Loss", 
                                        description=f"**{dice1} + {dice2} = {total}**\n**-{bet} coins**\nBalance: {new_balance}", 
                                        color=0xed4245)
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="crash", description="Multiplier crash game")
    @app_commands.describe(bet="Amount to bet")
    async def crash(self, interaction: discord.Interaction, bet: int):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 10:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 10 coins."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
            
            async with conn.transaction():
                new_balance = user['coins'] - bet
                await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
            
            crash_point = round(1.0 + (rng.generate(str(interaction.user.id)) * 9.0), 2)
            
            embed = discord.Embed(title="🚀 Crash Game", description="**1.00x**\nCash out before crash!", color=0x5865f2)
            view = CrashView(crash_point, bet, interaction.user.id, self.bot)
            await interaction.response.send_message(embed=embed, view=view)
            
            for i in range(1, 31):
                await asyncio.sleep(0.5)
                multiplier = round(1.0 + (i * 0.1), 2)
                
                if multiplier >= crash_point:
                    embed = discord.Embed(title="💥 CRASHED!", description=f"**{crash_point}x**\n**-{bet} coins**", color=0xed4245)
                    for item in view.children:
                        item.disabled = True
                    await interaction.edit_original_response(embed=embed, view=view)
                    break
                
                if view.cashed_out:
                    break
                
                embed.description = f"**{multiplier:.2f}x**\nCash out before crash!"
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except:
                    break
    
    @app_commands.command(name="slots", description="Slot machine")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if bet < 1:
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Min: 1 coin."))
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < bet:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {bet} coins."))
            
            symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣']
            reel1, reel2, reel3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
            
            win, multiplier = False, 0
            
            if reel1 == reel2 == reel3:
                win = True
                multiplier = 10 if reel1 == '7️⃣' else (5 if reel1 == '💎' else 3)
            elif reel1 == reel2 or reel2 == reel3:
                win, multiplier = True, 2
            
            async with conn.transaction():
                if win:
                    winnings = bet * multiplier
                    new_balance = user['coins'] + winnings
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'slots_win')
                    """, user['id'], winnings, new_balance)
                    embed = create_success_embed("🎰 Slots Win!", f"{reel1} {reel2} {reel3}\n\n**+{winnings} coins** ({multiplier}x)\nBalance: {new_balance}")
                else:
                    new_balance = user['coins'] - bet
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'slots_loss')
                    """, user['id'], bet, new_balance)
                    embed = discord.Embed(title="🎰 Slots", description=f"{reel1} {reel2} {reel3}\n\n**-{bet} coins**\nBalance: {new_balance}", color=0xed4245)
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="lottery", description="Buy lottery tickets")
    @app_commands.describe(tickets="Number of tickets (1-10, 100 coins each)")
    async def lottery(self, interaction: discord.Interaction, tickets: int):
        if not config.CASINO_REAL:
            return await interaction.response.send_message("🎰 Casino disabled.", ephemeral=True)
        
        if not (1 <= tickets <= 10):
            return await interaction.response.send_message(embed=create_error_embed("Invalid", "Buy 1-10 tickets."))
        
        cost = tickets * 100
        
        async with self.bot.db.acquire() as conn:
            user = await conn.fetchrow("SELECT id, coins FROM users WHERE discord_id = $1", str(interaction.user.id))
            if not user or user['coins'] < cost:
                return await interaction.response.send_message(embed=create_error_embed("Insufficient", f"Need {cost} coins."))
            
            wins = sum(1 for _ in range(tickets) if random.random() < 0.1)
            
            async with conn.transaction():
                if wins > 0:
                    winnings = wins * 500
                    new_balance = user['coins'] - cost + winnings
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'earn', $2, $3, 'lottery_win')
                    """, user['id'], winnings, new_balance)
                    embed = create_success_embed("🎟️ Lottery Winner!", 
                                                f"Tickets: {tickets}\nWinning: **{wins}**\n\n**+{winnings - cost} coins net**\nBalance: {new_balance}")
                else:
                    new_balance = user['coins'] - cost
                    await conn.execute("UPDATE users SET coins = $1 WHERE id = $2", new_balance, user['id'])
                    await conn.execute("""
                        INSERT INTO transactions (user_id, type, amount, balance_after, reason)
                        VALUES ($1, 'spend', $2, $3, 'lottery_loss')
                    """, user['id'], cost, new_balance)
                    embed = discord.Embed(title="🎟️ Lottery", 
                                        description=f"Tickets: {tickets}\nNo winners.\n\n**-{cost} coins**\nBalance: {new_balance}", 
                                        color=0xed4245)
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))
