import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sentry_sdk
import uuid

load_dotenv()
DSN = os.getenv("DSN")
sentry_sdk.init(dsn=DSN, traces_sample_rate=1.0)
DEVELOPER = int(os.getenv("DEV"))
error_dict = {}

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # ✅ Ignore CommandNotFound errors
        if isinstance(error, commands.CommandNotFound):
            return

        error_code = str(uuid.uuid4())[:8]  # short unique error code
        error_dict[error_code] = str(error)

        # Log to Sentry
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("user", str(ctx.author))
            scope.set_extra("command", ctx.message.content)
            scope.set_tag("error_code", error_code)
            sentry_sdk.capture_exception(error)

        # Send error embed to user
        embed = discord.Embed(
            title="⚠️ Command Error",
            description="An unexpected error has occurred. Please try again or contact support",
            color=discord.Color.orange()
        )
        embed.add_field(name="Error Code:", value=f"```{error_code}```", inline=False)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command()
    async def error(self, ctx, code: str):

        if DEVELOPER not in [role.id for role in ctx.author.roles]:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return

        if code in error_dict:
            embed = discord.Embed(
                title=f"Error {code}",
                description=f"**Error Details:**\n ```{error_dict[code]}```",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Invalid or expired error code.",
                color=discord.Color.dark_red()
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Error(bot))
