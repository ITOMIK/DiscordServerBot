@bot.command()
async def playAlbum(ctx, *args):

    name = ' '.join(args)

    if len(name.split("+")) != 2:
        guild_id = ctx.guild.id
        if guild_id not in queues:
            queues[guild_id] = []
        name = ' '.join(args)

        if len(name.split("+")) != 2:
            await ctx.send("Не удалось получить треки.")
        else:
            artist_name = name.split("+")[0]
            album_name = name.split("+")[1]
            tracks = await get_album_tracks(artist_name, album_name)
            print(artist_name, album_name, tracks)
            if tracks is not None:
                await ctx.send(f"Треки альбома '{album_name}' исполнителя '{artist_name}'добавлены в очередь")
                urls = []
                for track in tracks:
                    print("g")
                    t = await get_youtube_link(track, artist_name)
                    if t is not None:
                        #await play(ctx, t)  # Исправлено: Используйте await при вызове асинхронной функции
                        urls.append(t)

                for url in range(0,len(urls)-2):
                    yt = YouTube(urls[url])
                    stream = get_best_stream(yt.streams, "lowest")
                    if stream is None:
                        await ctx.send("No suitable streams found.")
                        return
                    audio_url = stream.url

                    queue.append(audio_url)

                await play(ctx, urls[-1])

            else:
                await ctx.send("Не удалось получить треки.")
