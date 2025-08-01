# server/economy.py

import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
import datetime
import os

DB_PATH = os.path.join("data", "economy.db")
os.makedirs("data", exist_ok=True)

# Initialize DB if not exists
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                last_daily TEXT
            )
        ''')

init_db()

# Helper to get or create user row
def get_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance, last_daily FROM economy WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.execute("INSERT INTO economy (user_id, balance, last_daily) VALUES (?, 0, NULL)", (user_id,))
            return 0, None
        return row

# Helper to update user data
def update_user(user_id, balance=None, last_daily=None):
    with sqlite3.connect(DB_PATH) as conn:
        if balance is not None and last_daily is not None:
            conn.execute("UPDATE economy SET balance = ?, last_daily = ? WHERE user_id = ?", (balance, last_daily, user_id))
        elif balance is not None:
            conn.execute("UPDATE economy SET balance = ? WHERE user_id = ?", (balance, user_id))
        elif last_daily is not None:
            conn.execute("UPDATE economy SET last_daily = ? WHERE user_id = ?", (last_daily, user_id))

# Dropdown View for coinflip
class CoinflipDropdown(discord.ui.Select):
    def __init__(self, bet_amount: int, user_id: int):
        self.bet_amount = bet_amount
        self.user_id = user_id
        
        options = [
            discord.SelectOption(label="Heads", description="Bet on heads", emoji="🪙"),
            discord.SelectOption(label="Tails", description="Bet on tails", emoji="🎯")
        ]
        
        super().__init__(placeholder="Choose heads or tails...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Make sure only the original user can interact
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your coinflip!", ephemeral=True)
            return
            
        guess = self.values[0].lower()
        bal, _ = get_user(self.user_id)
        
        # Double-check they still have enough balance
        if self.bet_amount > bal:
            await interaction.response.send_message("You don't have enough balls for this bet anymore!", ephemeral=True)
            return
        
        result = random.choice(["heads", "tails"])
        
        if guess == result:
            bal += self.bet_amount
            embed = discord.Embed(
                title="🎉 You Won!",
                description=f"The coin landed on **{result.title()}**!\nYou won **{self.bet_amount}** balls!",
                color=discord.Color.green()
            )
        else:
            bal -= self.bet_amount
            embed = discord.Embed(
                title="💸 You Lost!",
                description=f"The coin landed on **{result.title()}**!\nYou lost **{self.bet_amount}** balls.",
                color=discord.Color.red()
            )
        
        embed.add_field(name="New Balance", value=f"**{bal}** balls", inline=False)
        
        update_user(self.user_id, balance=bal)
        
        # Disable the dropdown after use
        self.disabled = True
        await interaction.response.edit_message(embed=embed, view=self.view)

class CoinflipView(discord.ui.View):
    def __init__(self, bet_amount: int, user_id: int):
        super().__init__(timeout=60.0)  # 60 second timeout
        self.add_item(CoinflipDropdown(bet_amount, user_id))
        self.user_id = user_id
    
    async def on_timeout(self):
        # Disable all items when view times out
        for item in self.children:
            item.disabled = True

def register_commands(bot):
    tree = bot.tree

    @tree.command(name="daily", description="Claim your daily balls")
    async def daily(interaction: discord.Interaction):
        user_id = interaction.user.id
        balance, last_daily = get_user(user_id)

        now = datetime.datetime.utcnow()
        if last_daily:
            last_time = datetime.datetime.fromisoformat(last_daily)
            if (now - last_time).total_seconds() < 86400:
                next_claim = last_time + datetime.timedelta(days=1)
                embed = discord.Embed(
                    title="⏰ Too Early!",
                    description=f"You already claimed your daily reward!\nCome back at `{next_claim.isoformat(timespec='minutes')}` UTC.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        reward = random.randint(100, 500)
        new_balance = balance + reward
        update_user(user_id, balance=new_balance, last_daily=now.isoformat())

        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You earned **{reward}** balls!",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"**{new_balance}** balls", inline=False)
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await interaction.response.send_message(embed=embed)

    @tree.command(name="coinflip", description="Bet on heads or tails")
    @app_commands.describe(bet="Amount to bet")
    async def coinflip(interaction: discord.Interaction, bet: int):
        bal, _ = get_user(interaction.user.id)
        
        if bet <= 0 or bet > bal:
            await interaction.response.send_message("Invalid bet amount.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🪙 Coinflip",
            description=f"You're betting **{bet}** balls!\nChoose heads or tails using the dropdown below.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Balance", value=f"**{bal}** balls", inline=False)
        
        view = CoinflipView(bet, interaction.user.id)
        
        try:
            await interaction.response.send_message(embed=embed, view=view)
        except (discord.errors.ConnectionClosed, discord.errors.HTTPException) as e:
            # Try to send a simpler fallback message if the embed/view fails
            try:
                await interaction.response.send_message(f"🪙 Coinflip started! Betting {bet} balls. (Simplified due to connection issues)")
            except:
                # If everything fails, at least log it
                print(f"Failed to send coinflip message for user {interaction.user.id}: {e}")

    @tree.command(name="rob", description="Rob another user")
    @app_commands.describe(victim="The user you want to rob")
    async def rob(interaction: discord.Interaction, victim: discord.Member):
        if victim.id == interaction.user.id:
            embed = discord.Embed(
                title="🤔 Nice Try!",
                description="You can't rob yourself, silly!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        thief_bal, _ = get_user(interaction.user.id)
        victim_bal, _ = get_user(victim.id)

        if victim_bal < 100:
            embed = discord.Embed(
                title="💸 Target Too Poor!",
                description=f"{victim.display_name} doesn't have enough balls to be worth robbing.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = random.random() < 0.5
        stolen = random.randint(50, min(200, victim_bal)) if success else 0

        if success:
            thief_bal += stolen
            victim_bal -= stolen
            embed = discord.Embed(
                title="🎭 Robbery Successful!",
                description=f"You successfully robbed **{stolen}** balls from {victim.display_name}!",
                color=discord.Color.green()
            )
        else:
            fine = random.randint(20, 100)
            thief_bal = max(0, thief_bal - fine)
            embed = discord.Embed(
                title="🚨 Caught Red-Handed!",
                description=f"You failed and got caught! You paid a fine of **{fine}** balls.",
                color=discord.Color.red()
            )
        
        embed.add_field(name="Your New Balance", value=f"**{thief_bal}** balls", inline=False)
        
        update_user(interaction.user.id, balance=thief_bal)
        update_user(victim.id, balance=victim_bal)
        
        await interaction.response.send_message(embed=embed)

    @tree.command(name="balls", description="Check someone's ball balance")
    @app_commands.describe(user="The user to check")
    async def balls(interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        bal, _ = get_user(target_user.id)
        
        if target_user.id == interaction.user.id:
            embed = discord.Embed(
                title="💰 Your Balance",
                description=f"You have **{bal}** balls in your pocket.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title=f"💰 {target_user.display_name}'s Balance",
                description=f"{target_user.display_name} has **{bal}** balls in their pocket.",
                color=discord.Color.blue()
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)