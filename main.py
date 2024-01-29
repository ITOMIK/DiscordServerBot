import asyncio
import time
import os
import requests

import yt_dlp
from pydub import AudioSegment
from pydub.playback import play

import discord
from discord import Member, VoiceChannel, Status
from discord.ext import commands
from threading import Thread

from discord.utils import get

with open(".env") as f: 
    for line in f:
        k,v = line.split("=")
        print(k,v)
        os.environ[k]=v


token = os.environ.get("DISCORD_BOT_TOKEN")
ffmpeg_path = r'D:\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe'

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY").strip()



intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Game(name="!helpme"))
deaf_members = []

def get_deaf(member: Member) -> bool:
    return member.voice.self_deaf


@bot.event
async def on_ready():
    bot.loop.create_task(move_deaf(get_deaf))
    print("started")


async def move_all(members: list[Member]):
    global deaf_members
    mem_ch: list[tuple[Member, int]] = [(mem, mem.voice.channel.id) for mem in members]
    for i in mem_ch:
        deaf_members.append(i)


@bot.command()
async def hello(ctx, member: discord.Member = None):  # Создаём функцию и передаём аргумент ctx.
    global deaf_members
    author = ctx.message.author  # Объявляем переменную author и записываем туда информацию об авторе.
    try:
        if member is None:
            await ctx.send(f"вы не ввели имя")
        else:
            if member.id in member.guild._voice_states.keys():
                if get_deaf(member):
                    deaf_members.append((member, member.voice.channel.id))
    except discord.ext.commands.errors.MemberNotFound(member):
        print("Пользователь не найден!")


@bot.command()
async def hello_all(ctx):
    global deaf_members
    print("hello_all")
    author: Member = ctx.message.author
    members = author.guild.voice_states.keys()
    mem_ch: list[tuple[Member, int]] = [(author.guild.get_member(mem), author.guild.get_member(mem).voice.channel.id)
                                        for mem in members]
    for i in mem_ch:
        deaf_members.append(i)


@bot.command()
async def helpme(ctx):
    await ctx.send(
        f"!hello @UserName - кидает из канала в канал ЗАМУЧЕНОГО человека до тех пор пока он не размутиться, !hello_all - кидает из канала в канал всех замученых, находящихся с вами в одном канале до тех пор, пока они не размутятся")

async def move_deaf(check_function):
    global deaf_members
    while True:
        for member in deaf_members:
            if not check_function(member[0]):
                await member[0].edit(voice_channel=member[0].guild.get_channel(member[1]))
                deaf_members.remove(member)
                continue
            await member[0].edit(voice_channel=member[0].guild.voice_channels[-1])
        await asyncio.sleep(1)
        for member in deaf_members:
            if not check_function(member[0]):
                await member[0].edit(voice_channel=member[0].guild.get_channel(member[1]))
                deaf_members.remove(member)
                continue
            await member[0].edit(voice_channel=member[0].guild.voice_channels[-2])
        await asyncio.sleep(1)

def get_album_tracks(artist, album):
    api_url = "http://ws.audioscrobbler.com/2.0/"
    api_key = "909c541b2a91ba2e708cdcf86513db32"

    params = {
        "method": "album.getinfo",
        "api_key": api_key,
        "artist": artist,
        "album": album,
        "format": "json",
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        tracks = data["album"]["tracks"]["track"]
        return [track["name"] for track in tracks]
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


@bot.command()
async def playAlbum(ctx, *args):
    name = ' '.join(args)
    print(len(name.split("+")), name.split("+"))

    if len(name.split("+")) != 2:
        await ctx.send("Не удалось получить треки.")
    else:
        artist_name = name.split("+")[0]
        album_name = name.split("+")[1]
        tracks = get_album_tracks(artist_name, album_name)
        print(artist_name, album_name)

        if tracks is not None:
            await ctx.send(f"Треки альбома '{album_name}' исполнителя '{artist_name}':")
            # Проверка, не находится ли бот уже в голосовом канале
           # if not ctx.voice_client:
            #    voice_channel_connection = await author_voice_channel.connect()
             #   await ctx.send(f"Бот подключен к голосовому каналу: {author_voice_channel.name}")
            author_voice_channel = ctx.author.voice.channel

            if not author_voice_channel:
                await ctx.send("Вы должны находиться в голосовом канале.")
                return

            # Подключение к голосовому каналу
            voice_channel_connection = await author_voice_channel.connect()
            #await ctx.send(f"Бот подключен к голосовому каналу: {author_voice_channel.name}")
            for track in tracks:
                await ctx.send(f"p! play {track}")
                # Отключение от голосового канала
            await voice_channel_connection.disconnect()
           # await ctx.send(f"Бот отключен от голосового канала.")

        else:
            await ctx.send("Не удалось получить треки.")



@bot.command()
async def play(ctx, url):
    # Используем yt-dlp для получения прямой ссылки на аудиофайл
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(info)
        audio_url = info['formats'][0]['url']

    # Используем discord.py для воспроизведения аудиофайла
    voice_channel = ctx.author.voice.channel
    voice_channel_connection = await voice_channel.connect()
    print(info)
    audio = AudioSegment.from_url(audio_url, format="mp3")
    play(audio)

    # Ожидаем завершения воспроизведения, прежде чем отключить бота от голосового канала
    while voice_channel_connection.is_playing():
        await asyncio.sleep(1)

    await voice_channel_connection.disconnect()

bot.run(token)
