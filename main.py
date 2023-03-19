import discord
from discord.ext import commands

token = 'MTA4MzczNzgwODYzNzc5NjQyMw.GpyRvD.rmMbEDcT9_rxYYfuExxUxCNQFfCG20jscPiaTc'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.command()
async def hello(ctx, member: discord.Member):  # Создаём функцию и передаём аргумент ctx.
    author = ctx.message.author  # Объявляем переменную author и записываем туда информацию об авторе.
    await ctx.send(f"name{member.nick}")
    if member.id in member.guild._voice_states.keys():
        is_mute = member.guild._voice_states[member.id].self_mute
        if is_mute:
            await member.edit(voice_channel=member.guild.voice_channels[1])


bot.run(token)
