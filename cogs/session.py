import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
from dotenv import load_dotenv
from discord import ui, ButtonStyle

import json

SESSION_FILE = "data\session_status.json"

def load_session_status():
    if not os.path.exists(SESSION_FILE):
        default = {
            "status": "Offline",
            "timestamp": int(datetime.now().timestamp()),
            "vote_started_by": None
        }
        save_session_status(default)
        return default
    with open(SESSION_FILE, "r") as f:
        return json.load(f)

def save_session_status(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

load_dotenv()
REQUIRED_ROLE_ID = int(os.getenv("REQUIRED_ROLE_ID"))
VOTE_LOG_CHANNEL_ID = int(os.getenv("VOTE_LOG_CHANNEL_ID"))
roles_to_ping = list(map(int, os.getenv("ROLE_TO_PING", "").split(",")))

SESSION_STATUS = load_session_status()


IMAGE_URLS = {
    "SSU": "https://cdn.discordapp.com/attachments/1341538724923572284/1401566320247574670/image.png?ex=6890bdda&is=688f6c5a&hm=cad4c9a2fdf17e65671f457051937f6e98ce9f5396cff133f8aba695f7a0b2b1&",
    "SSD": "https://cdn.discordapp.com/attachments/1341538724923572284/1401706567702806658/image.png?ex=68914078&is=688feef8&hm=654c389ff1d4e78c57b8a8c49aef035dba26e5517fd209cd93055cff3f759433&",
    "Full": "https://cdn.discordapp.com/attachments/1341538724923572284/1401566573541720124/image.png?ex=6890be16&is=688f6c96&hm=b8fbf53310dc3f798d2c81d7e4f648998b1406574fc818e4d0f6359d497c0b30&",
    "Boost": "https://cdn.discordapp.com/attachments/1341538724923572284/1401566573541720124/image.png?ex=6890be16&is=688f6c96&hm=b8fbf53310dc3f798d2c81d7e4f648998b1406574fc818e4d0f6359d497c0b30&",
    "Vote": "https://cdn.discordapp.com/attachments/1341538724923572284/1401566573541720124/image.png?ex=6890be16&is=688f6c96&hm=b8fbf53310dc3f798d2c81d7e4f648998b1406574fc818e4d0f6359d497c0b30&"
}

class SSULinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # or a custom timeout
        self.add_item(discord.ui.Button(
            label="Quick Join",
            style=ButtonStyle.link,
            url="https://policeroleplay.community/join/csrpx"
        ))


class VoteView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=None)
        self.voters = set()
        self.interaction = interaction
        self.message = None

    def get_embed(self):
        now = int(datetime.now().timestamp())
        vote_count = len(self.voters)
        voters_list = "\n".join([f"<@{uid}>" for uid in self.voters]) or "No votes yet."
        embed = discord.Embed(
            title="CSRPX | Session Vote",
            description=f"CSRP Management has decided to host an SSU poll. If you would like to join, press the checkmark below. Failing to join may result in moderation.",
            color=discord.Color.from_rgb(153,204,255)
        )
        embed.set_image(url=IMAGE_URLS["Vote"])
        embed.add_field(name="Vote Information", value=f">>> **Votes:** {vote_count}/6\n **Voters:** {voters_list}", inline=False)
        voter_id = SESSION_STATUS.get("vote_started_by")
        voter = self.message.guild.get_member(voter_id) if voter_id else None
        embed.add_field(name="Additional Information",
                        value=f">>> **Started At:** <t:{now}:F>\n **Started By:** {voter.mention if voter else 'Unknown'}",
                        inline=False)
        return embed

    @discord.ui.button(label="\u2705 Vote", style=discord.ButtonStyle.success, custom_id="vote_button")
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voters:
            self.voters.remove(interaction.user.id)
        else:
            self.voters.add(interaction.user.id)

        await self.message.edit(embed=self.get_embed(), view=self)
        await interaction.response.send_message("Your vote has been updated.", ephemeral=True)

class SessionDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Server Startup", value="SSU", emoji="\U0001F7E2"),
            discord.SelectOption(label="Server Shutdown", value="SSD", emoji="\u26D4"),
            discord.SelectOption(label="Server Full", value="Full", emoji="\U0001F5D3"),
            discord.SelectOption(label="Server Boost", value="Boost", emoji="\U0001F680"),
            discord.SelectOption(label="Server Vote", value="Vote", emoji="\U0001F5F3\uFE0F")
        ]
        super().__init__(placeholder="Choose an action", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        now = int(datetime.now().timestamp())
        channel = interaction.client.get_channel(VOTE_LOG_CHANNEL_ID)

        if choice == "SSU" and SESSION_STATUS["status"] in ("Offline", "Voting"):
            SESSION_STATUS["status"] = "Online"
            SESSION_STATUS["timestamp"] = now
            SESSION_STATUS["vote_started_by"] = None
            save_session_status(SESSION_STATUS)

            embed = discord.Embed(
                title="CSRPX | Session Startup",
                description="A session has commenced. Please make sure to read our in-game rules before joining <#1359181538436055061>\n ***Server Details***\n >>> Server Name: **California State Roleplay | Realistic | New**\n Server Code: [**CSRPX**](https://policeroleplay.community/join/CSRPX)\n Server Owner: **xxo_Angelx**",
                color=discord.Color.from_rgb(153, 204, 255)
            )
            embed.set_image(url=IMAGE_URLS["SSU"])


        elif choice == "SSD" and SESSION_STATUS["status"] == "Online":
            SESSION_STATUS["status"] = "Offline"
            SESSION_STATUS["timestamp"] = now
            SESSION_STATUS["vote_started_by"] = None
            save_session_status(SESSION_STATUS)
            embed = discord.Embed(
                title="CSRPX | Server Shutdown",
                description="Unfortunately our session has come to an end. If you attended we hope you enjoyed yourself!",
                color=discord.Color.red()
            )
            embed.set_image(url=IMAGE_URLS["SSD"])

            await interaction.response.edit_message(content="SSD has been selected.", embed=None, view=None)
            await channel.send(embed=embed)  # No role ping here
            return


        elif choice == "Full" and SESSION_STATUS["status"] == "Online":
            embed = discord.Embed(
                title="CSRPX | Session Full",
                description="Our server is full! Join for amazing roleplays as spots will open!",
                color=discord.Color.from_rgb(153, 204, 255)
            )
            embed.set_image(url=IMAGE_URLS["Full"])

            await interaction.response.edit_message(content="Full has been selected.", embed=None, view=None)
            await channel.send(embed=embed)  # No role ping here
            return

        elif choice == "Boost" and SESSION_STATUS["status"] == "Online":
            embed = discord.Embed(
                title="CSRPX | Server Boost",
                description="Our server is low on players. Join to help us get full and participate in engaging roleplays!",
                color=discord.Color.from_rgb(153, 204, 255)
            )
            embed.set_image(url=IMAGE_URLS["Boost"])


        elif choice == "Vote" and SESSION_STATUS["status"] == "Offline":
            SESSION_STATUS["status"] = "Voting"
            SESSION_STATUS["timestamp"] = now
            SESSION_STATUS["vote_started_by"] = interaction.user.id
            save_session_status(SESSION_STATUS)
            dummy_embed = discord.Embed(
                title="Loading...",
                description="Creating vote panel...",
                color=discord.Color.greyple()
            )

            dummy_message = await channel.send(embed=dummy_embed)

            vote_view = VoteView(interaction)  # no message yet

            # First send the vote panel with a placeholder embed or empty embed
            vote_panel = await channel.send(
                content="<@&1309110603419353088> | <@&1337620481645350953>",
                embed=discord.Embed(title="Loading..."),  # temporary placeholder
                view=vote_view
            )

            vote_view.message = vote_panel  # assign the real message now

            # Now generate the proper embed with message available
            embed = vote_view.get_embed()

            # Edit the message to update embed
            await vote_panel.edit(embed=embed, view=vote_view)

            await dummy_message.delete()

            await interaction.response.send_message("Vote started and posted in the vote log channel.", ephemeral=True)

            return


        else:
            await interaction.response.send_message("Invalid action based on current session status.", ephemeral=True)
            return

        await interaction.response.edit_message(content=f"{choice} has been selected.", embed=None, view=None)
        ping_str = " ".join(f"<@&{role_id}>" for role_id in roles_to_ping)
        await channel.send(content=ping_str, embed=embed)


class SessionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SessionDropdown())

class Session(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="session", description="Manage or view the current server session.")
    async def session(self, interaction: discord.Interaction):
        if REQUIRED_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        status = SESSION_STATUS["status"]
        timestamp = SESSION_STATUS["timestamp"]

        embed = discord.Embed(
            title="\U0001F4CB Session Panel",
            description=f"**Current Status:** {status}\n**Since:** <t:{timestamp}:R>",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=SessionView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Session(bot))
