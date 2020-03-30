import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

from spreadsheet import Sheet

sheet = Sheet("your_secret_json.json")
db = TinyDB('db.json')

client = commands.Bot(command_prefix="&", case_insensitive=True)

@client.command(name='setSheet')
@commands.has_permissions(administrator=True)
async def set_sheet(ctx, sheet_id, worksheet_name, player_range, discord_name_range,check_range):
    
    things_to_update = {"sheet_id": sheet_id, "worksheet_name": worksheet_name, "player_range": player_range, "discord_name_range": discord_name_range,"verify_range":check_range}
    db.table("guilds").update(things_to_update, Query().guild_id == ctx.guild.id)
    
    await ctx.send("kek")

@client.command(name='setBotChannel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx):

    db.table("guilds").update({"bot_channel":ctx.message.channel.id}, Query().guild_id == ctx.guild.id)
    await ctx.send(f"{str(ctx.message.channel)}has been set.")

def check_bot_channel(func):
    async def wrapper_check_bot_channel(ctx, *args,**kwargs):
        
        current_guild = db.table("guilds").get(Query().guild_id == ctx.guild.id)
        if ctx.message.channel.id == current_guild["bot_channel"]:
            await func(ctx, *args, **kwargs)
        else:
            correct_channel = discord.utils.get(ctx.guild.channels, id=current_guild["bot_channel"])
            await ctx.send(f"Wrong Channel, use {correct_channel.mention}")
    
    return wrapper_check_bot_channel


@client.command(name='verify')
@check_bot_channel
async def set_player(ctx, player_name):
    
    things_to_upsert = {"player_name":player_name, "player_discord_id": ctx.author.id, "guild_id": ctx.guild.id}
    db.table("players").upsert(things_to_upsert , (Query().player_discord_id == ctx.author.id) & (Query().guild_id == ctx.guild.id))

    sheet_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
    sheet.set_current_sheet_data(sheet_info["sheet_id"], sheet_info["worksheet_name"], sheet_info["player_range"], sheet_info["discord_name_range"], sheet_info["verify_range"])

    discord_user = discord.utils.get(ctx.guild.members, id=ctx.author.id)
    
    try:
        sheet.update_player(player_name, str(discord_user))
        await ctx.send("Player successfully verified!")
    except KeyError:
        await ctx.send(f"Player not found in the sheet.")
    
@client.command(name="roomSet")
async def create_qualifier(ctx, action, room_id):

    current_query =( (Query().guild_id == ctx.guild.id) & (Query().room_id == room_id) )

    if action == "add":
            
        if db.table("qualifier").contains(current_query):
            await ctx.send(f"There is already a room with the same id.")

        else:
            things_to_insert = {"room_id":room_id, "guild_id": ctx.guild.id, "players":[]}
            db.table("qualifier").insert(things_to_insert)
            await ctx.send(f"Qualifier room `{room_id}` successfully added.")

    elif action == "remove":

        if db.table("qualifier").contains(current_query):
            db.table("qualifier").remove(current_query)
            await ctx.send(f"Qualifier room `{room_id}` successfully deleted.")

        else:
            await ctx.send(f"Qualifier room `{room_id}` could not found")

@client.command(name="qualifier")
@check_bot_channel
async def join_rooms(ctx, action, room_id=""):

    current_player_name = db.table("players").get(Query().player_discord_id == ctx.author.id)["player_name"]
    old_room_query = Query().players.any(current_player_name)

    if action == "join":
        
        if room_id == "":
            await ctx.send("no room specified")
            return

        if db.table("qualifier").contains(old_room_query):
            await ctx.send("You are already in a room. To change rooms, use `&qualifier leave` command first.")
            return

        

        if not db.table("qualifier").contains(Query().room_id == room_id):
            await ctx.send(f"There is no room called `{room_id}`")
            return

        new_room = db.table("qualifier").get(Query().room_id == room_id)
        
        qualifier_room_size = 16
        if len(new_room["players"]) >= qualifier_room_size:
            await ctx.send("This room is full.")
            return

        new_room["players"].append(current_player_name)
        db.table("qualifier").update({"players":new_room["players"]},Query().room_id == room_id)
        await ctx.send(f"Player successfull added to room {room_id}")

    elif action == "leave":
        
        if db.table("qualifier").contains(old_room_query):
            old_room = db.table("qualifier").get(old_room_query)
            old_room["players"].remove(current_player_name)
            db.table("qualifier").update({"players":old_room["players"]},old_room_query)
            await ctx.send("Player Successfully removed.")
        else:
            await ctx.send("You aren't in any room. Use `&qualifier join` command.")
        

@client.command(name="qualifierRooms")
@check_bot_channel
async def show_rooms(ctx):
    
    rooms = db.table("qualifier").search(Query().guild_id == ctx.guild.id)

    desc_text = ""

    for room in rooms:
        player_String = ", ".join(room["players"])
        room_name = room["room_id"]
        desc_text += f"`{room_name}` - {player_String}\n"

    embeded = discord.Embed(title = "Qualifier Rooms", description=desc_text)
    await ctx.send(embed=embeded)


@client.command(name="ping")
async def ping_player(ctx, player_name):
    
    discord_id = db.table("players").get(Query().player_name == player_name)["player_discord_id"]
    await ctx.send(f"<@{discord_id}>")

@client.event
async def on_guild_join(guild):
    
    if db.table("guilds").contains(Query().guild_id == guild.id):
        print(f"i joined an old server called {guild.name}")
    else:
        things_to_insert = {"guild_id": guild.id, "sheet_id": None, "worksheet_name": None, "player_range": None, "discord_name_range":None, "check_range":None, "bot_channel":None }
        db.table("guilds").insert(things_to_insert)

        print(f"I joined {guild.name} for the first time!")

@client.event
async def on_ready():
    print(f"Bot Started!!")
    
    
client.run("TOKEN")