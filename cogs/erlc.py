import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ERLC_KEY")
MANAGEMENT_ROLE_ID = int(os.getenv("DEV"))

class Erlc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper: Get Roblox username by user ID
    def get_roblox_username(self, user_id):
        try:
            user_info = requests.get(f"https://users.roblox.com/v1/users/{user_id}")
            if user_info.status_code == 200:
                return user_info.json().get("name", "UnknownUser")
        except Exception:
            pass
        return "UnknownUser"

    # Hybrid command group: /erlc or !erlc
    @commands.hybrid_group(name="erlc", with_app_command=True)
    async def erlc(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand.")

    # Subcommand: /erlc players
    @erlc.command(name="players", help="Show current ERLC players")
    async def players(self, ctx):
        url = "https://api.policeroleplay.community/v1/server/players"
        headers = {
            "server-key": API_KEY,
            "Accept": "*/*"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not data:
                await ctx.send("No players currently online.")
                return

            description_lines = []
            for player_info in data:
                player_str = player_info.get("Player", "")
                team = player_info.get("Team", "Unknown")

                if ":" in player_str:
                    player_name, player_id = player_str.split(":", 1)
                else:
                    player_name = player_str
                    player_id = None

                if player_id and player_id.isdigit():
                    roblox_url = f"https://www.roblox.com/users/{player_id}/profile"
                    player_display = f"[{player_name}]({roblox_url})"
                else:
                    player_display = player_name

                description_lines.append(f"{player_display} ({team})")

            embed = discord.Embed(
                title="California State Roleplay | Current Players",
                description="\n".join(description_lines),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"{len(data)}/40 Players")
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1340879717464670279/2b3f56faa80e0e40c3eae192e8e5bf5d.png?size=512")
            await ctx.send(embed=embed)

        except requests.RequestException as e:
            await ctx.send(f"Error fetching player data: {e}")

    # Subcommand: /erlc serverinfo
    @erlc.command(name="serverinfo", help="Show ERLC server information")
    async def serverinfo(self, ctx):
        url = "https://api.policeroleplay.community/v1/server"
        headers = {
            "server-key": API_KEY,
            "Accept": "*/*"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            name = data.get("Name", "Unknown")
            join_key = data.get("JoinKey", "Unknown")
            current_players = data.get("CurrentPlayers", 0)
            max_players = data.get("MaxPlayers", 0)
            owner_id = data.get("OwnerId", None)
            co_owner_ids = data.get("CoOwnerIds", [])

            # Convert owner ID to username link
            def roblox_user_link(user_id):
                username = self.get_roblox_username(user_id)
                return f"[{username}](https://www.roblox.com/users/{user_id}/profile)"

            owner = roblox_user_link(owner_id) if owner_id else "Unknown"

            if co_owner_ids:
                co_owners = ", ".join([roblox_user_link(uid) for uid in co_owner_ids])
            else:
                co_owners = "None"

            embed = discord.Embed(
                title=f"{name}",
                color=discord.Color.from_rgb(153,204,255)
            )
            embed.add_field(
                name="Basic Info",
                value=f">>> **Join Code:** [{join_key}](https://policeroleplay.community/join/{join_key})\n**Current Players:** {current_players}/{max_players}\n**Queue:** 0",
                inline=False
            )
            embed.add_field(
                name="Server Ownership",
                value=f">>> **Owner:** {owner}\n**Co-Owners:** {co_owners}",
                inline=False
            )

            await ctx.send(embed=embed)

        except requests.RequestException as e:
            await ctx.send(f"Error fetching server info: {e}")

    @erlc.command(name="command", description="Send a command to the ERLC server.")
    @app_commands.describe(command="The ERLC command to send.")
    async def erlc_command(self, ctx: commands.Context, command: str):
        # Check if user has the Management role
        if not any(role.id == MANAGEMENT_ROLE_ID for role in ctx.author.roles):
            await ctx.reply("You do not have permission to use this command.", ephemeral=True)
            return

        # Try deferring if it's a slash command
        if ctx.interaction:
            await ctx.interaction.response.defer(thinking=True, ephemeral=True)

        try:
            response = requests.post(
                "https://api.policeroleplay.community/v1/server/command",
                headers={
                    "server-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={"command": f":{command}"}
            )
            data = response.json()

            msg = ""
            if response.status_code == 200:
                msg = f"Command sent: `{command}`\n**Response:** `{data.get('message', 'No message returned')}`"
            else:
                msg = f"❌ Failed to send command. Status: {response.status_code}"

            if ctx.interaction:
                await ctx.interaction.followup.send(msg)
            else:
                await ctx.send(msg)

        except Exception as e:
            if ctx.interaction:
                await ctx.interaction.followup.send(f"⚠️ Error while sending request: `{str(e)}`")
            else:
                await ctx.send(f"⚠️ Error while sending request: `{str(e)}`")


# Required setup function
async def setup(bot):
    await bot.add_cog(Erlc(bot))
