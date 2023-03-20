import time

import discord
from discord import Member, VoiceChannel, Status
from discord.ext import commands
from threading import Thread

token = 'MTA4MzczNzgwODYzNzc5NjQyMw.GpyRvD.rmMbEDcT9_rxYYfuExxUxCNQFfCG20jscPiaTc'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Game(name="!helpme"))
listOfMem = []

def get_deaf(member):
    return member.voice.self_deaf

def listeningMoveList(list):
    if(len(list)>0):
        for i in list:
            if(i.voice.self_deaf):
                move(i)
            else:
                list.remove(i)

async def move(member, check_function):
    channel = member.voice.channel.id
    while check_function(member):
        await member.edit(voice_channel=member.guild.voice_channels[-1])
        time.sleep(1)
        if not check_function(member):
            break
        await member.edit(voice_channel=member.guild.voice_channels[-2])
        time.sleep(1)
    await member.edit(voice_channel=member.guild.get_channel(channel))


async def move_all(members: list[Member], check_function):
    mem_ch: list[tuple[Member, int]] = [(mem, mem.voice.channel.id) for mem in members]
    while len(mem_ch) > 0:
        for member in mem_ch:
            if not check_function(member[0]):
                await member[0].edit(voice_channel=member[0].guild.get_channel(member[1]))
                mem_ch.remove(member)
                continue
            await member[0].edit(voice_channel=member[0].guild.voice_channels[-1])
        time.sleep(1)
        for member in mem_ch:
            if not check_function(member[0]):
                await member[0].edit(voice_channel=member[0].guild.get_channel(member[1]))
                mem_ch.remove(member)
                continue
            await member[0].edit(voice_channel=member[0].guild.voice_channels[-2])
        time.sleep(1)


thread1 = Thread(target=listeningMoveList, args=(listOfMem))

@bot.command()
async def hello(ctx, member : discord.Member = None):  # Создаём функцию и передаём аргумент ctx.
    author = ctx.message.author  # Объявляем переменную author и записываем туда информацию об авторе.
    try:
        if(member==None):
            await ctx.send(f"вы не ввели имя")
        else:
            if member.id in member.guild._voice_states.keys():
                if get_deaf(member):
                    listOfMem.append(member)
    except discord.ext.commands.errors.MemberNotFound(member):
            print("Пользователь не найден!")

@bot.command()
async def hello_all(ctx, ):
    author: Member = ctx.message.author
    members = author.guild.voice_states.keys()
    await move_all([author.guild.get_member(member_key) for member_key in members], get_deaf)

@bot.command()
async def helpme(ctx):
     await ctx.send(f"!hello @UserName - кидает из канала в канал ЗАМУЧЕНОГО человека до тех пор пока он не размутиться, !hello_all - кидает из канала в канал всех замученых, находящихся с вами в одном канале до тех пор, пока они не размутятся")    



bot.run(token)
