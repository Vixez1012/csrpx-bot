import discord
from discord.ext import commands
from jishaku.cog import Jishaku
from datetime import datetime
import os
import sentry_sdk
from dotenv import load_dotenv
from discord import Game, Activity, ActivityType
import requests
from logtail import LogtailHandler
import logging
import aiohttp
from discord.ext import tasks

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))  # Make sure this is a valid int
DSN = os.getenv("DSN")

BETTERSTACK_HEARTBEAT_URL = "https://uptime.betterstack.com/api/v1/heartbeat/dxBuxeiTyxd77wys1YaayL12"

# Initialize Sentry
sentry_sdk.init(
    dsn=DSN,
    send_default_pii=True,
)

# Allowed user IDs for Jishaku
ALLOWED_USERS = {
    614895781832556585  # Replace with your actual Discord ID(s)
}

# Intents setup
intents = discord.Intents.all()
intents.message_content = True

handler = LogtailHandler(
    source_token='EdrXD73AQ2wk9qSwjxyjKbiP',
    host='https://s1465045.eu-nbg-2.betterstackdata.com ',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(handler)


# Custom Jishaku cog that restricts access
class CustomJishaku(Jishaku):
    def __init__(self, bot):
        super().__init__(bot=bot)  # ✅ pass bot as keyword arg

    async def cog_check(self, ctx):
        return ctx.author.id in ALLOWED_USERS

# Custom bot class
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=">",
            intents=intents,
            application_id=None
        )
        self.synced = False

    async def setup_hook(self):
        cogs = [
            "cogs.accept",
            "cogs.market",
            "cogs.error",
            "cogs.erlc",
            "cogs.session",
            "cogs.staff",
            "cogs.say",
            "cogs.infractions",
            "cogs.music",
            "cogs.tts",
            "cogs.snipe",
            "cogs.ping",
            "cogs.ad",
            "cogs.afk"
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded cog: {cog}")
            except Exception as e:
                print(f"❌ Failed to load cog: {cog}")
                print(f"↪️ {type(e).__name__}: {e}")

        # Load restricted Jishaku (optional)
        await self.add_cog(CustomJishaku(self))

        if not self.synced:
            await self.tree.sync()
            self.synced = True

# Create the bot instance
bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    activity = Activity(type=ActivityType.watching, name="discord.gg/csrpx")
    await bot.change_presence(activity=activity)
    print("✅ Bot status updated.")

    # Try to send a "ready" message to a specific channel
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        timestamp = int(datetime.now().timestamp())
        await channel.send(f"Online as of <t:{timestamp}:F>")
    except discord.NotFound:
        print(f"❌ Channel with ID {CHANNEL_ID} not found.")
    except discord.Forbidden:
        print(f"🚫 Bot lacks permission to access the channel.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

    # ✅ Always attempt to start the ping loop after ready
    if not ping_betterstack.is_running():
        ping_betterstack.start()


@tasks.loop(minutes=2)
async def ping_betterstack():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BETTERSTACK_HEARTBEAT_URL) as response:
                if response.status == 200:
                    print("✅ Heartbeat sent to Better Stack.")
                else:
                    print(f"⚠️ Failed to send heartbeat: {response.status}")
        except Exception as e:
            print(f"❌ Error pinging Better Stack: {e}")

@bot.event
async def on_message(message: discord.Message):
    # Ignore bot's own messages
    if message.author.bot:
        return

    # Check if message is in a DM channel
    if isinstance(message.channel, discord.DMChannel):
        log_channel = bot.get_channel(CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📩 New DM Received",
                description=message.content,
                color=discord.Color.blue()
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"User ID: {message.author.id}")

            await log_channel.send(content="<@614895781832556585>", embed=embed)

    # Let other commands still work
    await bot.process_commands(message)

# Start the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ TOKEN not found in environment variables.")
