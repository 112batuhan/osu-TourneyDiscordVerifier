import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

from spreadsheet import Sheet

sheet = Sheet("your_secret_json_file.json")
db = TinyDB('db.json')

client = commands.Bot(command_prefix="&", case_insensitive=True)

@client.command(name='setSheet')
@commands.has_permissions(administrator=True)
async def set_sheet(ctx, sheet_id, worksheet_name, player_range, discord_name_range,check_range):
    
    things_to_update = {"sheet_id": sheet_id, "worksheet_name": worksheet_name, "player_range": player_range, "discord_name_range": discord_name_range,"verify_range":check_range}
    db.table("guilds").update(things_to_update, Query().guild_id == ctx.guild.id)
    
    await ctx.send("kek")

@client.command(name='verify')
async def set_player(ctx, player_name):
    
    things_to_upsert = {"player_name":player_name, "player_discord_id": ctx.author.id, "guild_id": ctx.guild.id}
    db.table("players").upsert(things_to_upsert , Query().player_discord_id == ctx.author.id)

    sheet_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
    sheet.set_current_sheet_data(sheet_info["sheet_id"], sheet_info["worksheet_name"], sheet_info["player_range"], sheet_info["discord_name_range"], sheet_info["verify_range"])

    discord_user = discord.utils.get(ctx.guild.members, id=ctx.author.id)
    
    try:
        sheet.update_player(player_name, str(discord_user))
        await ctx.send("Player successfully verified!")
    except KeyError:
        await ctx.send(f"Player not found.")
    
@client.command(name="ping")
async def ping_player(ctx, player_name):
    
    discord_id = db.table("players").get(Query().player_name == player_name)["player_discord_id"]
    await ctx.send(f"<@{discord_id}>")

@client.event
async def on_guild_join(guild):
    
    if db.table("guilds").contains(Query().guild_id == guild.id):
        print(f"i joined an old server called {guild.name}")
    else:
        things_to_insert = {"guild_id": guild.id, "sheet_id": None, "worksheet_name": None, "player_range": None, "discord_name_range":None, "check_range":None }
        db.table("guilds").insert(things_to_insert)

        print(f"I joined {guild.name} for the first time!")

@client.event
async def on_ready():
    print(f"Bot Started!!")
    
    
client.run("Token")