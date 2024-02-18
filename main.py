import asyncio
import os
import requests
import random
from pydub.playback import play
from youtubesearchpython import VideosSearch

import re
import discord
from discord import Member
from discord.ext import commands

from pytube import YouTube

with open(".env") as f: 
    for line in f:
        k,v = line.split("=")
        os.environ[k]=v


token = os.environ.get("DISCORD_BOT_TOKEN")
ffmpeg_path = r'D:\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe'

url_pattern = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)(?P<video_id>[^\?&\"\'<>]+)$'

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY").strip()

queues = {}

_queues ={}

rightNamesOfTracks = {
    "8 Cпособов": "8 Способов Как Бросить ...",
    "8 способов": "8 Способов Как Бросить ..."
}

queue = []
isQueues = {}
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
async def helloAll(ctx):
    global deaf_members
    print("hello_all")
    author: Member = ctx.message.author
    members = author.guild._voice_states.keys()
    mem_ch: list[tuple[Member, int]] = [(author.guild.get_member(mem), author.guild.get_member(mem).voice.channel.id)
                                        for mem in members]
    for i in mem_ch:
        deaf_members.append(i)


async def get_youtube_link(name):

    if name:
        # Step 3: Use YouTube API to search for the video link
        videos_search = VideosSearch(f"{name}", limit = 1)
        results = videos_search.result()

        # Step 4: Extract the YouTube link
        if 'result' in results and results['result']:
            youtube_link = results['result'][0]['link']
            print(youtube_link)
            return youtube_link


    return None



@bot.command()
async def helpme(ctx):
    await ctx.send(
        f">>> **!hello @UserName - кидает из канала в канал ЗАМУЧЕНОГО человека до тех пор пока он не размутиться**\n**!hello_all - кидает из канала в канал всех замученых, находящихся с вами в одном канале до тех пор, пока они не размутятся**\n**!play <link>/<name> - бот играет аудио из любого ютуб видео**\n**!skip - пропустить текущую песню**\n**!stop - остановить бота**\n**!playRadio <LastFMUsername> - воспроизводит популярные треки с вашего ластфм аккаунта песни играют до добавления прочих в очередь**\n**!forcePlay <name>/<link> - скипает текущий трек и добавляет данный в начало очереди**\n**!playAlbum <albumName> - воспроизводит весь альбом**")

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


async def _play(ctx, url, quality="lowest"):
    try:
        guild_id = ctx.guild.id
        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in isQueues:
            isQueues[guild_id] = False
        if (isQueues[guild_id] == True):
            await ctx.send("**Дождитесь загрузки предыдущего альбома(это проблема api youtube)**")
            return
        # If the bot is not in a voice channel, connect to the user's channel
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            voice_channel_connection = await voice_channel.connect()
        else:
            voice_channel_connection = ctx.voice_client

        # Use pytube to get the audio URL
        yt = YouTube(url)
        stream = get_best_stream(yt.streams, quality)
        if stream is None:
            await ctx.send("**Ошибка при нахождении потока.**")
            return

        audio_url = stream.url

        # Add the track to the queue
        await ctx.send(f"> **Трек добавлен в очередь**")
        queues[guild_id].append(audio_url)


        # If the bot is not currently playing, start playing from the queue
        if not voice_channel_connection.is_playing():
            await play_queue(ctx, voice_channel_connection)
    except Exception as e:
        print(f"Error extracting audio URL: {e}")
        await ctx.send(f"**Ошибка при добавление трека/альбома**")
        return


@bot.command()
async def play(ctx, *args):
    name = ' '.join(args)
    if len(name)<=0:
        await ctx.send("**Не удалось получить треки.**")
    else:
        if re.match(url_pattern, name):
            await _play(ctx, name)
        else:
            track = await get_youtube_link(name)
            if track is not None:
                await _play(ctx, track)



@bot.command()
async def playAlbum(ctx, *args):
    try:
        _name = ' '.join(args)
        guild_id = ctx.guild.id
        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in isQueues:
            isQueues[guild_id] = False
        if (isQueues[guild_id] == True):
            await ctx.send("**Дождитесь загрузки предыдущего альбома(это проблема api youtube)**")
            return
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            voice_channel_connection = await voice_channel.connect()
        else:
            voice_channel_connection = ctx.voice_client

        name = await search_album(_name)

        if len(name.split("+")) != 2:
            await ctx.send("**Не удалось получить треки.**")
        else:
            artist_name = name.split("+")[0]
            album_name = name.split("+")[1]
            tracks = await get_album_tracks(artist_name, album_name)
            if tracks is not None:
                global IsQueue
                isQueues[guild_id] = True
                number = 1
                await ctx.send(f"> **Треки альбома {album_name} исполнителя {artist_name} добавляются в очередь:**")
                for track in tracks:
                    t = await get_youtube_link(track+" "+artist_name)
                    if t is not None:
                        yt = YouTube(t)
                        stream = get_best_stream(yt.streams, "lowest")
                        if stream is None:
                            await ctx.send("**Ошибка при нахождении потока.**")
                            return
                        audio_url = stream.url
                        queues[guild_id].append(audio_url)
                        await ctx.send(f"```ansi\n [1;2m[1;31m[1;32m{number}.[0m[1;31m[0m [1;36m{artist_name}[0m - [1;33m[1;34m{track}[0m[1;33m[0m[0m\n```")
                        number+=1
                        # If the bot is not currently playing, start playing from the queue
                        if not voice_channel_connection.is_playing():
                            asyncio.create_task(play_queue(ctx, voice_channel_connection))
                            #await play_queue(ctx, voice_channel_connection)
                isQueues[guild_id] = False
                # If the bot is not currently playing, start playing from the queue
                if not voice_channel_connection.is_playing():
                    await play_queue(ctx, voice_channel_connection)
            else:
                await ctx.send("**Не удалось получить треки.**")
    except Exception as e:
        print(f"Error extracting audio URL: {e}")
        await ctx.send(f"**Ошибка при добавление трека/альбома**")
        return


async def search_album(albumname):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    method = "album.search"
    params = {
        "album": albumname,
        "api_key": LASTFM_API_KEY,
        "method": method,
        "format": "json"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        result = data["results"]["albummatches"]["album"]
        if(len(result)>0):
            for key, value in rightNamesOfTracks.items():
                if(result[0]["name"].startswith(key)):
                    result[0]["name"]=value
            answ = result[0]["artist"]+"+"+result[0]["name"]
            return answ

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None
async def get_chart():
    base_url = "http://ws.audioscrobbler.com/2.0/"
    method = "chart.gettoptracks"
    params = {
        "api_key": LASTFM_API_KEY,
        "method": method,
        "format": "json"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        tracks = data["tracks"]["track"]
        result = [{"artist": track["artist"]["name"], "track": track["name"]} for track in tracks]
        random.shuffle(result)
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

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
async def autoPlay(ctx):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if guild_id not in isQueues:
        isQueues[guild_id] = False
    if (isQueues[guild_id] == True):
        await ctx.send("**Дождитесь загрузки предыдущего альбома(это проблема api youtube)**")
        return
    try:
        if ctx.voice_client and ctx.voice_client.is_playing():
            queues[guild_id].clear()
            ctx.voice_client.stop()
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            voice_channel_connection = await voice_channel.connect()
        else:
            voice_channel_connection = ctx.voice_client
        tracks = await get_chart()
        if tracks is not None:
            isQueues[guild_id] = True
            await ctx.send(f"> **Играет Топ Чарт LastFM:**")
            for track in tracks:
                if(ctx.voice_client is None):
                    return
                t = await get_youtube_link(track['track'] + " " + track['artist'])
                if t is not None:
                    yt = YouTube(t)
                    stream = get_best_stream(yt.streams, "lowest")
                    if stream is None:
                        await ctx.send("**Ошибка при нахождении потока.**")
                        return
                    audio_url = stream.url
                    queues[guild_id].append(audio_url)
                    await ctx.send(f"```ansi\n [0m[1;31m[0m [1;36m{track['artist']}[0m [1;33m[1;34m- {track['track']}[0m[1;33m[0m[0m\n```")
                    if not voice_channel_connection.is_playing():
                        await play_queue(ctx, voice_channel_connection)
            isQueues[guild_id] = False
        else:
            await ctx.send("**Не удалось получить треки.**")
    except Exception as e:
        if (isQueues[guild_id] == True):
            print(f"Error extracting audio URL: {e}")
            await ctx.send(f"**Ошибка при добавление трека/альбома**")
        return


@bot.command()
async def playRadio(ctx, name):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if guild_id not in isQueues:
        isQueues[guild_id] = False
    if (isQueues[guild_id] == True):
        await ctx.send("**Дождитесь загрузки предыдущего альбома(это проблема api youtube)**")
        return
    try:
        if ctx.voice_client and ctx.voice_client.is_playing():
            queues[guild_id].clear()
            ctx.voice_client.stop()
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            voice_channel_connection = await voice_channel.connect()
        else:
            voice_channel_connection = ctx.voice_client
        tracks = await get_top_tracks(name)
        if tracks is not None:
            isQueues[guild_id] = True
            await ctx.send(f"> **Радио пользователя {name}:**")
            for track in tracks:
                if(ctx.voice_client is None):
                    return
                t = await get_youtube_link(track['track']+" "+track['artist'])
                if t is not None:
                    yt = YouTube(t)
                    stream = get_best_stream(yt.streams, "lowest")
                    if stream is None:
                        await ctx.send("**Ошибка при нахождении потока.**")
                        return
                    audio_url = stream.url
                    queues[guild_id].append(audio_url)
                    await ctx.send(f"```ansi\n [0m[1;31m[0m [1;36m{track['artist']}[0m [1;33m[1;34m- {track['track']}[0m[1;33m[0m[0m\n```")
                    if not voice_channel_connection.is_playing():
                        await play_queue(ctx, voice_channel_connection)
            isQueues[guild_id] = False
        else:
            await ctx.send("**Не удалось получить треки.**")
    except Exception as e:
        if (isQueues[guild_id] == True):
            print(f"Error extracting audio URL: {e}")
            await ctx.send(f"**Ошибка при добавление трека/альбома**")
        return



@bot.command()
async def forcePlay(ctx,*args):
    name = ' '.join(args)
    if len(name) <= 0:
        await ctx.send("**Не удалось получить трек**")
        return
    guild_id = ctx.guild.id
    if guild_id not in isQueues:
        isQueues[guild_id] = False
    if (isQueues[guild_id] == True):
        await ctx.send("**Дождитесь загрузки предыдущего альбома(это проблема api youtube)**")
        return
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
        url = None
        # Use pytube to get the audio URL
        if re.match(url_pattern, name):
            url = name
        else:
            track = await get_youtube_link(name)
            if track is not None:
                url = track
        yt = YouTube(url)
        stream = get_best_stream(yt.streams, quality)
        if stream is None:
            await ctx.send("**Ошибка при нахождении потока.**")
            return

        audio_url = stream.url

        # Add the track to the queue
        await ctx.send(f"**Трек добавлен в очередь**")
        queues[guild_id].insert(0, audio_url)
    except Exception as e:
        print(f"Error extracting audio URL: {e}")
        await ctx.send(f"**Ошибка при добавление трека/альбома**")
        return
    await skip(ctx)
    # If the bot is not currently playing, start playing from the queue
    if not voice_channel_connection.is_playing():
        await play_queue(ctx, voice_channel_connection)

@bot.command()
async def skip(ctx):
    # Skip the current track
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("**Пропущен текущий трек.**")
    else:
        await ctx.send("**Ничего не играет.**")


@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if guild_id not in isQueues:
        isQueues[guild_id] = False
    isQueues[guild_id] = False
    # Stop playback and clear the queue
    if ctx.voice_client:
        queues[guild_id].clear()
        ctx.voice_client.stop()
        await ctx.send("**Остановка и отчистка очереди**")
        #await ctx.voice_client.disconnect()
    else:
        await ctx.send("**Бот не находится в канале**")


async def play_queue(ctx, voice_channel_connection):
    guild_id = ctx.guild.id
    if guild_id not in isQueues:
        isQueues[guild_id] = False
    if guild_id not in queues:
        queues[guild_id] = []
    while queues[guild_id]:
        track_url = queues[guild_id].pop(0)
        audio_source = discord. FFmpegPCMAudio(source=track_url,before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",options="-vn")
        if(ctx.voice_client is not None):
            voice_channel_connection.play(audio_source)

        # Wait for the track to finish playing
        while voice_channel_connection.is_playing():
            await asyncio.sleep(1)

        # Disconnect from the voice channel after the queue is empty
    if not voice_channel_connection.is_playing() and not isQueues[guild_id]:
        if voice_channel_connection:
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
