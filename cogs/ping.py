import discord
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency: `{latency_ms}ms`**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
