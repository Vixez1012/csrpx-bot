import discord
from discord.ext import commands
from discord import app_commands
import time
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Replace this with your actual API key
load_dotenv()
REQUIRED_ROLE_ID = int(os.getenv("IA"))
STAFF_CHANNEL_ID = int(os.getenv("STAFF_CHANNEL_ID"))
API_KEY = os.getenv("ERLC_KEY")

# Cooldown tracker
last_staffrequest_time = 0

def get_erlc_player_count():
    try:
        response = requests.get(
            "https://api.policeroleplay.community/v1/server",
            headers={
                "server-key": API_KEY,
                "Accept": "*/*"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("CurrentPlayers", 0)
    except Exception as e:
        print(f"[ERLC API ERROR] {e}")
        return 0  # fallback if API call fails

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="request", help="Request for staff to join the server.")
    @app_commands.describe(reason="Reason for staff.")
    async def staffrequest(self, ctx: commands.Context, *, reason: str):
        global last_staffrequest_time

        # Role check
        if REQUIRED_ROLE_ID not in [role.id for role in ctx.author.roles]:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return

        # Cooldown check
        current_time = time.time()
        if current_time - last_staffrequest_time < 1800:
            remaining = int((1800 - (current_time - last_staffrequest_time)) // 60)
            await ctx.send(f"This command is on cooldown. Try again in {remaining} minute(s).", ephemeral=True)
            return

        # Set cooldown
        last_staffrequest_time = current_time

        # Get current time and player count
        timestamp = int(time.time())
        player_count = get_erlc_player_count()

        # Build embed
        embed = discord.Embed(
            title="🚨 Staff Assistance Requested",
            description=f"A new staff request has been sent by {ctx.author.mention} ({ctx.author.id})",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Request Information",
            value=(
                f">>> **Reason:** {reason}\n"
                f"**In-Game Players:** {player_count}/40\n"
                f"**Requested By:** {ctx.author.mention}\n"
                f"**Time:** <t:{timestamp}:F> (<t:{timestamp}:R>)"
            )
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # Send messages
        await ctx.send("✅ Your request has been submitted.", ephemeral=True)
        await self.bot.get_channel(STAFF_CHANNEL_ID).send(
            content="<@&1308841437248360549> | <@&1308841425906958367>",
            embed=embed
        )

async def setup(bot):
    await bot.add_cog(Staff(bot))
