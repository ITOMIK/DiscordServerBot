import asyncio


@bot.command()


def my_async_function():
    pass


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
                    await ctx.send(f"{artist_name} - {track}")
                    # If the bot is not currently playing, start playing from the queue
                    if not voice_channel_connection.is_playing():
                        asyncio.create_task(play_queue(ctx, voice_channel_connection))
                        #await play_queue(ctx, voice_channel_connection)
            IsQueue = False
            # If the bot is not currently playing, start playing from the queue
            if not voice_channel_connection.is_playing():
                await play_queue(ctx, voice_channel_connection)

        else:
            await ctx.send("Не удалось получить треки.")