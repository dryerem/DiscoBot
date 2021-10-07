import discord
import sys
from discord.channel import VoiceChannel

from discord.ext import commands, tasks
from discord import VoiceClient, FFmpegPCMAudio, Member
from discord.ext.commands.core import Command, command

import youtube_dl

import random
import asyncio
import os

import pafy

import youtube_playlist as pl

bot = commands.Bot(command_prefix='--')

start_path: str = os.path.abspath(os.path.dirname(__file__))
ffmpeg_path: str = os.path.normpath(os.path.join(start_path, 'ffmpeg/win64/bin/'))
outtmpl: str = os.path.normpath(os.path.join(start_path, 'downloads/audio'))

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)



class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTS), data=data)


class Disco(commands.Cog):
    def __init__(self, bot, youtube_token: str) -> None:
        self.bot: commands.Bot = bot
        self._youtube_token = youtube_token

        self.queue = []

        self.tasks = []


        self.source: FFmpegPCMAudio = None

        self.current_playing_track: str = "Сейчас ничего не играет" #  трек, который играет сейчас

        self.voice_client: VoiceClient = None
        self.ctx: commands.Context = None


    @commands.command()
    async def join(self, ctx: commands.Context):
        """Joins a voice channel """

        audio: list = os.listdir(start_path + '/audio')

        author: Member = ctx.message.author
        channel: VoiceChannel = ctx.author.voice.channel
        self.voice_client = await channel.connect()
        self.voice_client.play(FFmpegPCMAudio(executable='ffmpeg', source=start_path + f'/audio/{random.choice(audio)}'), after=None)

    @commands.command()
    async def leave(self, ctx: commands.Context):
        """Leave a voice channel"""

        voice_client: VoiceClient = ctx.voice_client
        if voice_client is None:
            await ctx.send('The bot is not connected to a voice channel')
        else:
            await ctx.voice_client.disconnect()
            self.tasks.clear()
            self.track_position = 0

    @commands.command()
    async def play(self, ctx: commands.Context, url: str = None):
        """add to the play queue or reproduce now if the queue is empty"""
        
        if ctx.voice_client is None:
            self.voice_client = await ctx.author.voice.channel.connect()

        if self.voice_client.is_paused() and url is None:
            self.voice_client.play(self.source)
            await ctx.send(f'Сейчас играет: {self.current_playing_track}')
        
        if 'list=' in url:
            playlist: list = pl.playlist_parse(url, token=self._youtube_token)
            self.tasks.extend(playlist)
        else:
            with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
                info: dict = ydl.extract_info(url, download=False)

            title: str = info.get('title')
            audio_url: str = info.get('url')
            self.tasks.append((audio_url, title))
            await ctx.send(f"Добавлено в очередь: {title}, номер в очереди: {len(self.tasks)}")            

        if self.voice_client.is_playing() is False and self.voice_client.is_paused() is False:
            self.current_playing_track = self.tasks[0][1]
            self.source = FFmpegPCMAudio(executable='ffmpeg', source=self.tasks.pop(0)[0], **FFMPEG_OPTS)
            self.voice_client.play(self.source, after=lambda x=None: self.check_queue(ctx))
            await ctx.send(f'Сейчас играет: {self.current_playing_track}')

    @commands.command()
    async def next(self, ctx: commands.Context):
        """Go to the next track"""
        
        if self.voice_client.is_paused():
            self.voice_client.resume()
        
        self.voice_client.stop()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pauses a track"""

        self.voice_client.pause()
        await ctx.send(f'Поставлен на паузу: {self.current_playing_track}')

    @commands.command()
    async def queue(self, ctx: commands.Context):
        """Displays the play queue list"""

        if len(self.tasks) > 0:
            await ctx.send(''.join([f'Позиция: {i + 1}, трек: ' + x[1] + "\n" for i, x in enumerate(self.tasks)]))
        else:
            await ctx.send('В очереди нет треков')

    @commands.command()
    async def current(self, ctx: commands.Context):
        """what song is playing now"""

        await ctx.send(f'Сейчас играет: {self.current_playing_track}')

    @commands.command()
    async def goto(self, ctx: commands.Context, pos: int):
        """Jump to position, tell the queue number"""

        pos = pos - 1
        if 0 <= pos < len(self.tasks):
            await self.voice_client.disconnect()
            channel: VoiceChannel = ctx.author.voice.channel
            self.voice_client = await channel.connect()

            self.current_playing_track = self.tasks[pos][1]
            self.source = FFmpegPCMAudio(executable='ffmpeg', source=self.tasks.pop(0)[0], **FFMPEG_OPTS)
            self.voice_client.play(self.source, after=lambda x=None: self.check_queue(ctx))

            await ctx.send(f'Сейчас играет: {self.current_playing_track}')
        else:
            await ctx.send(f'Позиция не найдена!')

    def check_queue(self, ctx: commands.Context):
        if len(self.tasks) > 0 and self.voice_client.is_connected():
            title: str = self.tasks[0][1]
            self.source = FFmpegPCMAudio(executable='ffmpeg', source=self.tasks.pop(0)[0], **FFMPEG_OPTS)
            ctx.voice_client.play(self.source, after=lambda x=None: self.check_queue(ctx))
            self.bot.loop.create_task(ctx.send(f"Проигрывается: {title}"))
            self.current_playing_track = title


if __name__ == "__main__":

    from configparser import ConfigParser
    from sys import argv, exit
    from os import path

    file_config: str = None
    for iter, arg in enumerate(argv):
        if arg == '--config':
            file_config = argv[iter + 1]
    
    config: ConfigParser = ConfigParser()
    if file_config:
        if path.isfile(file_config):
            config.read(file_config)
        else:
            print("File config not found!")
            exit(1)
    else:
        start_path: str = path.abspath(path.dirname(__file__))
        file_config = path.normpath(path.join(start_path, 'config.ini'))
        if path.isfile(file_config):
            config.read(file_config)
        else:
            print("File config not found!")
            exit(1)

    discord_token: str = config['Discord']['token']
    youtube_token: str = config['Youtube']['token']

    bot = commands.Bot(command_prefix='-', description='Disco bot')
    bot.add_cog(Disco(bot, youtube_token))
    bot.run(discord_token)