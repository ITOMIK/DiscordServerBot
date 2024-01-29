import asyncio
import time
import os
import requests
import random
import yt_dlp
from pydub import AudioSegment
from pydub.playback import play
from youtubesearchpython import VideosSearch

import discord
from discord import Member, VoiceChannel, Status
from discord.ext import commands
from threading import Thread

from discord.utils import get

from pytube import YouTube

with open(".env") as f: 
    for line in f:
        k,v = line.split("=")
        print(k,v)
        os.environ[k]=v


token = os.environ.get("DISCORD_BOT_TOKEN")
ffmpeg_path = r'D:\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe'

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY").strip()

queues = {}

queue = []

IsQueue = False
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


async def get_youtube_link(track_name, artist_name):

    if track_name and artist_name:
        # Step 3: Use YouTube API to search for the video link
        videos_search = VideosSearch(f"{artist_name} {track_name}", limit = 1)
        results = videos_search.result()

        # Step 4: Extract the YouTube link
        if 'result' in results and results['result']:
            youtube_link = results['result'][0]['link']
            return youtube_link

    return None



@bot.command()
async def helpme(ctx):
    await ctx.send(
        f"!hello @UserName - кидает из канала в канал ЗАМУЧЕНОГО человека до тех пор пока он не размутиться\n!hello_all - кидает из канала в канал всех замученых, находящихся с вами в одном канале до тех пор, пока они не размутятся\n!play <link> - бот играет аудио из любого ютуб видео\n!playSong <nameOfSong>+<NameOfArtist> - включает трек по названию и исполнителю\n!skip - пропустить текущую песню\n!stop - остановить бота\n!playRadio <LastFMUsername> - воспроизводит популярные треки с вашего ластфм аккаунта\n!forsePlay <link> - скипает текущий трек и добавляет данный в начало очереди")

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

async def get_album_tracks(artist, album):

    params = {
        "method": "album.getinfo",
        "api_key": LASTFM_API_KEY,
        "artist": artist,
        "album": album,
        "format": "json",
    }

    try:
        response = requests.get(LASTFM_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        tracks = data["album"]["tracks"]["track"]
        return [track["name"] for track in tracks]
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

@bot.command()
async def play(ctx, url, quality="lowest"):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    # If the bot is not in a voice channel, connect to the user's channel
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        voice_channel = ctx.author.voice.channel
        voice_channel_connection = await voice_channel.connect()
    else:
        voice_channel_connection = ctx.voice_client

    try:
        # Use pytube to get the audio URL
        yt = YouTube(url)
        stream = get_best_stream(yt.streams, quality)
        if stream is None:
            await ctx.send("No suitable streams found.")
            return

        audio_url = stream.url

        # Add the track to the queue
        await ctx.send(f"Трек добавлен в очередь {queues}")
        queues[guild_id].append(audio_url)
    except Exception as e:
        print(f"Error extracting audio URL: {e}")
        return

    # If the bot is not currently playing, start playing from the queue
    if not voice_channel_connection.is_playing():
        await play_queue(ctx, voice_channel_connection)


@bot.command()
async def playSong(ctx, *args):
    name = ' '.join(args)
    if len(name.split("+")) != 2:
        await ctx.send("Не удалось получить треки.")
    else:
        artist_name = name.split("+")[0]
        track_name = name.split("+")[1]
        track = await get_youtube_link(track_name, artist_name)
        if track is not None:
            await play(ctx, track)
@bot.command()
async def playAlbum(ctx, *args):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        voice_channel = ctx.author.voice.channel
        voice_channel_connection = await voice_channel.connect()
    else:
        voice_channel_connection = ctx.voice_client

    name = ' '.join(args)

    if len(name.split("+")) != 2:
        await ctx.send("Не удалось получить треки.")
    else:
        artist_name = name.split("+")[0]
        album_name = name.split("+")[1]
        tracks = await get_album_tracks(artist_name, album_name)
        print(artist_name, album_name,tracks )

        if tracks is not None:
            global IsQueue
            IsQueue = True
            await ctx.send(f"Треки альбома '{album_name}' исполнителя '{artist_name}'добавлены в очередь")
            for track in tracks:
                t = await get_youtube_link(track, artist_name)
                if t is not None:
                    yt = YouTube(t)
                    stream = get_best_stream(yt.streams, "lowest")
                    if stream is None:
                        await ctx.send("No suitable streams found.")
                        return
                    audio_url = stream.url
                    queues[guild_id].append(audio_url)
                    # If the bot is not currently playing, start playing from the queue
                    if not voice_channel_connection.is_playing():
                        await play_queue(ctx, voice_channel_connection)
            IsQueue = False
            # If the bot is not currently playing, start playing from the queue
            if not voice_channel_connection.is_playing():
                await play_queue(ctx, voice_channel_connection)

        else:
            await ctx.send("Не удалось получить треки.")


async def get_top_tracks(username):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    method = "user.gettoptracks"
    params = {
        "user": username,
        "api_key": LASTFM_API_KEY,
        "method": method,
        "format": "json"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        tracks = data["toptracks"]["track"]

        # Extracting relevant information
        result = [{"artist": track["artist"]["name"], "track": track["name"]} for track in tracks]

        # Shuffle the list randomly
        random.shuffle(result)

        return result

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

@bot.command()
async def playRadio(ctx, name):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        voice_channel = ctx.author.voice.channel
        voice_channel_connection = await voice_channel.connect()
    else:
        voice_channel_connection = ctx.voice_client
    tracks = await get_top_tracks(name)
    if tracks is not None:
        global IsQueue
        IsQueue = True
        for track in tracks:
            t = await get_youtube_link(track['track'], track['artist'])
            print(t)
            if t is not None:
                yt = YouTube(t)
                stream = get_best_stream(yt.streams, "lowest")
                if stream is None:
                    await ctx.send("No suitable streams found.")
                    return
                audio_url = stream.url
                queues[guild_id].append(audio_url)
                # If the bot is not currently playing, start playing from the queue
                if not voice_channel_connection.is_playing():
                    await play_queue(ctx, voice_channel_connection)
        IsQueue = False
            # If the bot is not currently playing, start playing from the queue
        if not voice_channel_connection.is_playing():
            await play_queue(ctx, voice_channel_connection)

    else:
        await ctx.send("Не удалось получить треки.")



@bot.command()
async def forsePlay(ctx,url):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    quality = "lowest"
    # If the bot is not in a voice channel, connect to the user's channel
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        voice_channel = ctx.author.voice.channel
        voice_channel_connection = await voice_channel.connect()
    else:
        voice_channel_connection = ctx.voice_client

    try:
        # Use pytube to get the audio URL
        yt = YouTube(url)
        stream = get_best_stream(yt.streams, quality)
        if stream is None:
            await ctx.send("No suitable streams found.")
            return

        audio_url = stream.url

        # Add the track to the queue
        await ctx.send(f"Трек добавлен в очередь ")
        queues[guild_id].insert(0, audio_url)
    except Exception as e:
        print(f"Error extracting audio URL: {e}")
        return
    global IsQueue
    IsQueue = True
    await skip(ctx)
    # If the bot is not currently playing, start playing from the queue
    if not voice_channel_connection.is_playing():
        await play_queue(ctx, voice_channel_connection)
    IsQueue = False

@bot.command()
async def skip(ctx):
    # Skip the current track
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current track.")
    else:
        await ctx.send("No track is currently playing.")


@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    # Stop playback and clear the queue
    if ctx.voice_client:
        ctx.voice_client.stop()
        queues[guild_id].clear()
        await ctx.send("Stopped playback and cleared the queue.")
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("The bot is not currently in a voice channel.")


async def play_queue(ctx, voice_channel_connection):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    while queues[guild_id]:
        track_url = queues[guild_id].pop(0)
        audio_source = discord.FFmpegPCMAudio(track_url)
        voice_channel_connection.play(audio_source)

        # Wait for the track to finish playing
        while voice_channel_connection.is_playing():
            await asyncio.sleep(1)

    # Disconnect from the voice channel after the queue is empty
    if not voice_channel_connection.is_playing() and not IsQueue:
        #print(IsQueue)
        await voice_channel_connection.disconnect()


def get_best_stream(streams, quality):
    if quality.lower() == "highest":
        return streams.get_highest_resolution()
    elif quality.lower() == "lowest":
        return streams.get_lowest_resolution()
    else:
        for stream in streams:
            if quality.lower() in str(stream):
                return stream
        return None



bot.run(token)
