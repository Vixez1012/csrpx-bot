import discord
from discord.ext import commands
from discord import app_commands


ALLOWED_ROLES = [1341321216870449172,1341271047642546176,1341275605131464776,1341279574368976908]

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="say", description="Say something as the bot.")
    @app_commands.describe(message="The message to say")
    async def say(self, ctx: commands.Context, *, message: str):
        if not any(role.id in ALLOWED_ROLES for role in ctx.author.roles):
            await ctx.reply("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            if ctx.message:
                await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
            await ctx.channel.send(message)
            await ctx.interaction.followup.send("Message sent.", ephemeral=True)
        else:
            await ctx.channel.send(message)
            await ctx.send("✅ Message sent.")


async def setup(bot):
    await bot.add_cog(Say(bot))
