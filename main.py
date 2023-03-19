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
    muted = []
    for mem in member.guild._voice_states:
        state = member.guild._voice_states[mem]
        if state.self_mute:
            muted.append(mem)
    await ctx.send(muted)


bot.run(token)
