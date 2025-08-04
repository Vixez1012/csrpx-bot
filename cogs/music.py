import discord
from discord.ext import commands
import yt_dlp
import asyncio

ytdl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.volume = {}  # guild_id: volume level (0.0 to 2.0)

    async def search_youtube(self, query):
        info = ytdl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info['title']

    async def play_next(self, ctx):
        if self.song_queue.get(ctx.guild.id):
            url, title = self.song_queue[ctx.guild.id].pop(0)
            volume = self.volume.get(ctx.guild.id, 1.0)
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=volume)
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(f"🎶 Now playing: **{title}**")
        else:
            await ctx.voice_client.disconnect()

    @commands.command()
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ You're not connected to a voice channel.")

        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client:
            if voice_client.channel == voice_channel:
                return await ctx.send("ℹ️ I'm already in your voice channel.")
            else:
                await voice_client.disconnect()

        await asyncio.sleep(1)  # prevent 4006 by slowing the handshake
        await voice_channel.connect()
        await ctx.send("🎶 Joined the voice channel!")

    @commands.command()
    async def play(self, ctx, *, search: str):
        if not ctx.voice_client:
            await self.join(ctx)
            await asyncio.sleep(1)

        url, title = await self.search_youtube(search)

        guild_id = ctx.guild.id
        if guild_id not in self.song_queue:
            self.song_queue[guild_id] = []

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.song_queue[guild_id].append((url, title))
            await ctx.send(f"📥 Added to queue: **{title}**")
        else:
            volume = self.volume.get(guild_id, 1.0)
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=volume)
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(f"🎧 Now playing: **{title}**")

    @commands.command()
    async def queue(self, ctx):
        queue = self.song_queue.get(ctx.guild.id, [])
        if not queue:
            return await ctx.send("📭 Queue is empty.")

        msg = "\n".join([f"{i + 1}. {title}" for i, (_, title) in enumerate(queue)])
        await ctx.send(f"🎵 **Queue:**\n{msg}")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped the song.")
        else:
            await ctx.send("❌ Nothing is playing.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left the voice channel.")
            self.song_queue.pop(ctx.guild.id, None)
        else:
            await ctx.send("❌ I'm not in a voice channel.")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused playback.")
        else:
            await ctx.send("❌ Nothing is playing.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed playback.")
        else:
            await ctx.send("❌ Nothing is paused.")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.song_queue[ctx.guild.id] = []
            await ctx.send("⏹️ Stopped playback and cleared the queue.")
        else:
            await ctx.send("❌ I'm not in a voice channel.")

    @commands.command()
    async def volume(self, ctx, level: int):
        """Set playback volume (1–200%)."""
        if not 1 <= level <= 200:
            return await ctx.send("❌ Volume must be between 1 and 200.")

        self.volume[ctx.guild.id] = level / 100
        await ctx.send(f"🔊 Volume set to **{level}%**")

        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.send("ℹ️ New volume will apply on the next song.")


async def setup(bot):
    await bot.add_cog(Music(bot))
