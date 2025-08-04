import discord
from discord.ext import commands
import asyncio

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        self.sniped_messages[message.channel.id] = {
            "content": message.content or "*[Embed/Attachment]*",
            "author": message.author,
            "time": message.created_at,
            "userid": message.author.id
        }


        await asyncio.sleep(60)
        self.sniped_messages.pop(message.channel.id, None)

    @commands.hybrid_command(name="snipe", help="Retrieves the most recent deleted message.")
    async def snipe(self, ctx):
        data = self.sniped_messages.get(ctx.channel.id)
        if not data:
            return await ctx.send("There's nothing to snipe!")

        embed = discord.Embed(
            description=f"Message deleted by <@{data['userid']}> has been sniped.",
            color=discord.Color.red(),
            timestamp=data["time"]
        )
        embed.add_field(name="Content:", value=data["content"])
        embed.set_author(name=f"Snipped by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Snipe(bot))
