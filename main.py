from http.server import executable
import discord
from discord import voice_client

from discord.ext import commands
from discord import VoiceClient, AudioSource, FFmpegPCMAudio

import youtube_dl
import os

#client = discord.Client()

bot = commands.Bot(command_prefix='--')

start_path: str = os.path.abspath(os.path.dirname(__file__))
ffmpeg_path: str = os.path.normpath(os.path.join(start_path, 'ffmpeg/win64/bin/'))
outtmpl: str = os.path.normpath(os.path.join(start_path, 'downloads/audio'))

ydl_opts = {'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
            }],
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': outtmpl
}
# with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#     ydl.download(['http://www.youtube.com/watch?v=BaW_jenozKc'])

# @client.event
# async def on_ready():
#     print('We have logged in as {0.user}'.format(client))

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return

#     if message.content.startswith('--play'):
#         voice = VoiceClient(client, "Сериальчики")
#         await voice.connect(timeout=10, reconnect=True)

#         await client.voice_clients.
#         #await message.channel.send('денис любит дашу @sdd!')


@bot.command(pass_context=True)
async def on_message(message):
    if message.author == bot.user:
        return

    print(message)


@bot.command(name='join')
async def join(ctx):
    author = ctx.message.author
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='stop')
async def leave(ctx):
    if ctx.message.guild.voice_client.is_connected():
        await ctx.voice_client.disconnect()
    else:
        await ctx.send('The bot is not connected to a voice channel')

@bot.command(name='play')
async def play(ctx: commands.Context, url: str):
    servername: str = ctx.message.guild
    voice_channel = ctx.author.voice.channel


    channel = ctx.author.voice.channel

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    voice_client: VoiceClient = await channel.connect()
    audio_source: FFmpegPCMAudio = FFmpegPCMAudio(executable=os.path.normpath(os.path.join(ffmpeg_path, 'ffmpeg.exe')), 
        source=os.path.normpath(os.path.join(start_path, 'downloads/audio.mp3')))
    voice_client.play(source=audio_source, after=None)
    

# @play.error
# async def play_error(ctx: commands.Context, error: commands.CommandError, ):
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send("Please, specify url adress")

bot.run('ODg5NDk1NTk4ODEyNzcwMzU2.YUiFVA.gbUO2j-ZBuCEViC14CRw6l28iuU')