import discord
from discord.ext import commands

token= 'MTA4MzczNzgwODYzNzc5NjQyMw.GpqysK.n84zB1andiXpBCFAUIbWwgBj98F4eRbOQLkZXQ'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = '!', intents=intents)

@bot.command()  
async def hello(ctx, member : discord.Member): # Создаём функцию и передаём аргумент ctx.
    author = ctx.message.author # Объявляем переменную author и записываем туда информацию об авторе.
    await ctx.send(f"name{member.nick}")

bot.run(token) 
