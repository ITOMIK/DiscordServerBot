import datetime
import os
import json
import asyncio
import discord

last_processed_entries = {}

async def check_audit_logs(bot, guild_id, start_time):
    await bot.wait_until_ready()
    guild = bot.get_guild(guild_id)
    while not bot.is_closed():
        async for entry in guild.audit_logs(limit=10):
            if entry.action in [discord.AuditLogAction.member_update, discord.AuditLogAction.channel_update]:
                if entry.id in last_processed_entries and last_processed_entries[entry.id] >= start_time:
                    continue
                print(entry.created_at)
                if entry.action == discord.AuditLogAction.member_update:
                    decrease_reputation(guild_id, entry.target.id, 10)
                    print(f"Пользователь {entry.user} изменил настройки участника {entry.target}")
                elif entry.action == discord.AuditLogAction.channel_update:
                    decrease_reputation(guild_id, entry.user.id, 5)
                    print(f"Пользователь {entry.user} изменил канал {entry.target}")
                last_processed_entries[entry.id] = datetime.datetime.now()
        await asyncio.sleep(20)

def decrease_reputation(server_id, user_id, amount):
    filename = "reputation.json"
    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            json.dump({}, file)

    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except json.decoder.JSONDecodeError:
        print("aaa")
        data = {}

    if server_id not in data:
        data[server_id] = {'users': {}}

    server_data = data[server_id]

    if user_id not in server_data['users']:
        server_data['users'][user_id] = {'reputation': 0}

    server_data['users'][user_id]['reputation'] -= amount

    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)
        print("Репутация пользователя успешно обновлена.")
    except Exception as e:
        print(f"Ошибка при записи в файл {filename}: {e}")