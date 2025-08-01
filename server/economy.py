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

def get_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance, last_daily FROM economy WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.execute("INSERT INTO economy (user_id, balance, last_daily) VALUES (?, 0, NULL)", (user_id,))
            return 0, None
        return row

def update_user(user_id, balance=None, last_daily=None):
    with sqlite3.connect(DB_PATH) as conn:
        if balance is not None and last_daily is not None:
            conn.execute("UPDATE economy SET balance = ?, last_daily = ? WHERE user_id = ?", (balance, last_daily, user_id))
        elif balance is not None:
            conn.execute("UPDATE economy SET balance = ? WHERE user_id = ?", (balance, user_id))
        elif last_daily is not None:
            conn.execute("UPDATE economy SET last_daily = ? WHERE user_id = ?", (last_daily, user_id))

class BallFlipDropdown(discord.ui.Select):
    def __init__(self, bet_amount: int, user_id: int):
        self.bet_amount = bet_amount
        self.user_id = user_id
        
        options = [
            discord.SelectOption(label="Heads", description="Bet on heads", emoji="🪙"),
            discord.SelectOption(label="Tails", description="Bet on tails", emoji="🎯")
        ]
        
        super().__init__(placeholder="Choose heads or tails...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your ballflip!", ephemeral=True)
            return
            
        guess = self.values[0].lower()
        bal, _ = get_user(self.user_id)
        
        if self.bet_amount > bal:
            await interaction.response.send_message("You don't have enough balls for this bet anymore!", ephemeral=True)
            return
        
        result = random.choice(["heads", "tails"])
        
        if guess == result:
            bal += self.bet_amount
            embed = discord.Embed(
                title="You Won! :3",
                description=f"The coin landed on **{result.title()}**!\nYou won **{self.bet_amount}** balls!",
                color=discord.Color.green()
            )
        else:
            bal -= self.bet_amount
            embed = discord.Embed(
                title="You Lost! :[",
                description=f"The coin landed on **{result.title()}**!\nYou lost **{self.bet_amount}** balls.",
                color=discord.Color.red()
            )
        
        embed.add_field(name="New Balance", value=f"**{bal}** balls", inline=False)
        
        update_user(self.user_id, balance=bal)
        
        self.disabled = True
        await interaction.response.edit_message(embed=embed, view=self.view)

class BallFlipView(discord.ui.View):
    def __init__(self, bet_amount: int, user_id: int):
        super().__init__(timeout=60.0)  # 60 second timeout
        self.add_item(BallFlipDropdown(bet_amount, user_id))
        self.user_id = user_id
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class LeaderboardView(discord.ui.View):
    def __init__(self, bot, total_pages: int, current_page: int = 0):
        super().__init__(timeout=120.0)
        self.bot = bot
        self.total_pages = total_pages
        self.current_page = current_page
        
        self.update_buttons()
    
    def update_buttons(self):
        self.clear_items()
        
        prev_button = discord.ui.Button(
            label="< Previous", 
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == 0)
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        page_button = discord.ui.Button(
            label=f"Page {self.current_page + 1}/{self.total_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True
        )
        self.add_item(page_button)
        
        next_button = discord.ui.Button(
            label="Next >", 
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == self.total_pages - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = await self.create_leaderboard_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = await self.create_leaderboard_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def create_leaderboard_embed(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, balance 
                FROM economy 
                WHERE balance > 0 
                ORDER BY balance DESC 
                LIMIT 10 OFFSET ?
            """, (self.current_page * 10,))
            users = cur.fetchall()
        
        embed = discord.Embed(
            title="Ball Leaderboard",
            description="People with the most BALLS!",
            color=discord.Color.gold()
        )
        
        if not users:
            embed.add_field(
                name="No Data", 
                value="No users found on this page.", 
                inline=False
            )
            return embed
        
        leaderboard_text = ""
        start_rank = self.current_page * 10 + 1
        
        for i, (user_id, balance) in enumerate(users):
            rank = start_rank + i
            
            try:
                user = await self.bot.fetch_user(user_id)
                username = user.display_name
            except:
                username = f"Unknown User ({user_id})"
            
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            else:
                medal = f"**{rank}.**"
            
            leaderboard_text += f"{medal} {username} - **{balance:,}** balls\n"
        
        embed.add_field(
            name=f"Rankings {start_rank}-{start_rank + len(users) - 1}",
            value=leaderboard_text,
            inline=False
        )
        
        embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages}")
        
        return embed
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

def register_commands(bot):
    tree = bot.tree

    @tree.command(name="leaderboard", description="View the ball leaderboard")
    async def leaderboard(interaction: discord.Interaction):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM economy WHERE balance > 0")
            total_users = cur.fetchone()[0]
        
        if total_users == 0:
            embed = discord.Embed(
                title="Ball Leaderboard",
                description="No users have any balls yet! Use `/daily` to get started!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        total_pages = (total_users + 9) // 10
        
        view = LeaderboardView(bot, total_pages)
        embed = await view.create_leaderboard_embed()
        
        await interaction.response.send_message(embed=embed, view=view)

    @tree.command(name="daily", description="Claim your daily balls :>")
    async def daily(interaction: discord.Interaction):
        user_id = interaction.user.id
        balance, last_daily = get_user(user_id)

        now = datetime.datetime.utcnow()
        if last_daily:
            last_time = datetime.datetime.fromisoformat(last_daily)
            if (now - last_time).total_seconds() < 86400:
                next_claim = last_time + datetime.timedelta(days=1)
                embed = discord.Embed(
                    title="Too Early!",
                    description=f"You already claimed your daily reward!\nCome back at `{next_claim.isoformat(timespec='minutes')}` UTC.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        reward = random.randint(100, 500)
        new_balance = balance + reward
        update_user(user_id, balance=new_balance, last_daily=now.isoformat())

        embed = discord.Embed(
            title="Daily Reward Claimed!",
            description=f"You earned **{reward}** balls!",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"**{new_balance}** balls", inline=False)
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await interaction.response.send_message(embed=embed)

    @tree.command(name="ballflip", description="Bet on heads or tails")
    @app_commands.describe(bet="Amount to bet")
    async def ballflip(interaction: discord.Interaction, bet: int):
        bal, _ = get_user(interaction.user.id)
        
        if bet <= 0 or bet > bal:
            await interaction.response.send_message("Invalid bet amount.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🏀 Ballflip",
            description=f"You're betting **{bet}** balls!\nChoose heads or tails using the dropdown below.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Balance", value=f"**{bal}** balls", inline=False)
        
        view = BallFlipView(bet, interaction.user.id)
        
        try:
            await interaction.response.send_message(embed=embed, view=view)
        except (discord.errors.ConnectionClosed, discord.errors.HTTPException) as e:
            try:
                await interaction.response.send_message(f"🏀 Ballflip started! Betting {bet} balls.")
            except:
                print(f"Failed to send ballflip message for user {interaction.user.id}: {e}")

    @tree.command(name="rob", description="Rob another user")
    @app_commands.describe(victim="The user you want to rob")
    async def rob(interaction: discord.Interaction, victim: discord.Member):
        if victim.id == interaction.user.id:
            embed = discord.Embed(
                title="Nice Try! XD",
                description="You can't rob yourself, silly!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        thief_bal, _ = get_user(interaction.user.id)
        victim_bal, _ = get_user(victim.id)

        if victim_bal < 100:
            embed = discord.Embed(
                title="Target Too Poor!",
                description=f"{victim.display_name} is too broke to be robbed dude.",
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
                title="Robbery Successful!",
                description=f"You successfully robbed **{stolen}** balls from {victim.display_name}! (shame on u, but ok)",
                color=discord.Color.green()
            )
        else:
            fine = random.randint(20, 100)
            thief_bal = max(0, thief_bal - fine)
            embed = discord.Embed(
                title="Caught Red-Handed!",
                description=f"You got an insane skill issue, so you paid a fine of **{fine}** balls.",
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
                title="Your Balance",
                description=f"You have **{bal}** BALLS.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title=f"{target_user.display_name}'s Balance",
                description=f"{target_user.display_name} has **{bal}** BALLS.",
                color=discord.Color.blue()
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)