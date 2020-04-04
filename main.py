import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

from spreadsheet import Sheet

sheet = Sheet("osutournamentdiscordjoincheck-84f8d6e67c81.json")
db = TinyDB('db.json')
client = commands.Bot(command_prefix="&", case_insensitive=True)

@client.command(name='setSheet')
@commands.has_permissions(administrator=True)
async def set_sheet(ctx, sheet_id, worksheet_name, player_range, discord_name_range,check_range):
    """
    Sets the registration sheet.

    sheet_id: ID of the sheet.
    worksheet_name: Name of the sheet in the spreadsheet.
    player_range: Range of the player column in A1 notation.
    discord_name_range: Range of the discord tags column in A1 notation.
    check_range: Range of the checkbox column in A1 notation.

    """
    things_to_update = {"sheet_id": sheet_id, "worksheet_name": worksheet_name, "player_range": player_range, "discord_name_range": discord_name_range,"verify_range":check_range}
    db.table("guilds").update(things_to_update, Query().guild_id == ctx.guild.id)
    
    await ctx.send("Registration sheet has been set.")

@client.command(name='setBotChannel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx):
    """
    Sets the bot channel and limits certain commands there.
    """

    db.table("guilds").update({"bot_channel":ctx.message.channel.id}, Query().guild_id == ctx.guild.id)
    await ctx.send(f"{str(ctx.message.channel)}has been set.")

def check_bot_channel(func):
    async def wrapper_check_bot_channel(ctx, *args,**kwargs):
        
        current_guild = db.table("guilds").get(Query().guild_id == ctx.guild.id)
        if current_guild["bot_channel"] == None:
            await ctx.send("Bot channel hasn't been set yet. Use `&setBotChannel` command in the channel you want to be set.")
        elif ctx.message.channel.id == current_guild["bot_channel"]:
            await func(ctx, *args, **kwargs)
        else:
            correct_channel = discord.utils.get(ctx.guild.channels, id=current_guild["bot_channel"])
            await ctx.send(f"Wrong Channel, use {correct_channel.mention}")
    
    return wrapper_check_bot_channel

@client.command(name='addVerifiedPlayers')
async def add_players_in_bulk(ctx):

    sheet_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
    sheet.set_current_sheet_data(sheet_info["sheet_id"], sheet_info["worksheet_name"], sheet_info["player_range"], sheet_info["discord_name_range"], sheet_info["verify_range"])
    verified_player_data = sheet.get_player_list()

    none_list = []

    for player in verified_player_data:
        
        discord_name, discord_tag = player[1].split("#")
        discord_user = discord.utils.get(ctx.guild.members, name=discord_name, discriminator=discord_tag)

        if discord_user == None:
            none_list.append(f"`{player[0]}` | `{player[1]}`")
        else:
            things_to_upsert = {"player_name":player[0], "player_discord_id": discord_user.id, "guild_id": ctx.guild.id}
            db.table("players").upsert(things_to_upsert , (Query().player_discord_id == discord_user.id) & (Query().guild_id == ctx.guild.id))

    if len(none_list)>0:
        await ctx.send(f"These players couldn't be find in the server:\n"+ "\n".join(none_list[:10]) +" \nThey might have changed their discord information after signing up.")
    
@client.command(name='verify')
async def set_player(ctx, player_name):
    """
    Verifies a player in the sheet.

    player_name: Players in game name.
    """

    discord_user = discord.utils.get(ctx.guild.members, id=ctx.author.id)
    
    try:

        sheet_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
        sheet.set_current_sheet_data(sheet_info["sheet_id"], sheet_info["worksheet_name"], sheet_info["player_range"], sheet_info["discord_name_range"], sheet_info["verify_range"])
        sheet.update_player(player_name, str(discord_user))

        things_to_upsert = {"player_name":player_name, "player_discord_id": ctx.author.id, "guild_id": ctx.guild.id}
        db.table("players").upsert(things_to_upsert , (Query().player_discord_id == ctx.author.id) & (Query().guild_id == ctx.guild.id))

        await ctx.send("Player successfully verified!")

    except KeyError:
        await ctx.send(f"Player not found in the sheet.")

    
    
@client.command(name="roomSet")
@commands.has_permissions(administrator=True)
async def create_qualifier(ctx, action, room_id):
    """
    Sets up a qualifier room.

    action: add or remove
    room_id: name of the room.
    """

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

@client.command(name="qualifier")#maybe rewrite this later, it turned into spagetti a bit
async def join_rooms(ctx, action, room_id=""):
    """
    Joining or leaving a qualifier room.

    action: join or leave
    room_id: Name of the room when joining.
    """

    current_player = db.table("players").get(Query().player_discord_id == ctx.author.id)
    
    if current_player == None:#rewrite the table.get functions into this, i wasn't aware that i could do this.
        await ctx.send("You are not a verified player.")
        return

    old_room_query = Query().players.any(current_player["player_name"])

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

        new_room["players"].append(current_player["player_name"])
        db.table("qualifier").update({"players":new_room["players"]},Query().room_id == room_id)
        await ctx.send(f"Player successfull added to room {room_id}")

    elif action == "leave":
        
        if db.table("qualifier").contains(old_room_query):
            old_room = db.table("qualifier").get(old_room_query)
            old_room["players"].remove(current_player["player_name"])
            db.table("qualifier").update({"players":old_room["players"]},old_room_query)
            await ctx.send("Player Successfully removed.")
        else:
            await ctx.send("You aren't in any room. Use `&qualifier join` command.")
        

@client.command(name="qualifierRooms")
async def show_rooms(ctx):
    """
    Shows the qualifier rooms.
    """
    
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
    """
    pings a player with their in game name.

    player_name: In game name of the player.
    """
    
    discord_id = db.table("players").get(Query().player_name.lower() == player_name.lower())["player_discord_id"]
    await ctx.send(f"{ctx.author.mention} pings <@{discord_id}>")

@client.event
async def on_guild_join(guild):
    
    if db.table("guilds").contains(Query().guild_id == guild.id):
        print(f"i joined an old server called {guild.name}")
    else:
        things_to_insert = {"guild_id": guild.id, "sheet_id": None, "worksheet_name": None, "player_range": None, "discord_name_range":None, "verify_range":None, "bot_channel":None }
        db.table("guilds").insert(things_to_insert)

        print(f"I joined {guild.name} for the first time!")


@client.event
async def on_ready():
    print(f"Bot Started!!")
    
    
client.run("Token")