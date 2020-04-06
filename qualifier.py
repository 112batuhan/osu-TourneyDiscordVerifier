import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

from spreadsheet import Sheet

sheet = Sheet("osutournamentdiscordjoincheck-84f8d6e67c81.json")
db = TinyDB('db.json')

class Qualifier(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="roomSet")
    @commands.has_permissions(administrator=True)
    async def create_qualifier(self, ctx, action, room_id, day="",time=""):
        """
        Sets up a qualifier room.

        action: add or remove
        room_id: name of the room.
        """

        qualifier_settings = db.table("guilds").get(Query().guild_id == ctx.guild.id)["qualifier_sheet_settings"]
            
        if qualifier_settings != None:
            pass
        else:
            await ctx.send(f"Qualifier sheet settings unknown. Use `&setQualifierSheet` command first.")
            return

        current_query = ((Query().guild_id == ctx.guild.id) & (Query().room_id == room_id))

        if action == "add":
                
            if db.table("qualifier").contains(current_query):
                await ctx.send(f"There is already a room with the same id.")
            else:
                
                things_to_insert = {"room_id":room_id, "guild_id": ctx.guild.id, "players":[], "day":day, "time":time, "referee":"", "mp_link":""}
                db.table("qualifier").insert(things_to_insert)
                await ctx.send(f"Qualifier room `{room_id}` successfully added.")

        elif action == "remove":

            if db.table("qualifier").contains(current_query):
                
                
                db.table("qualifier").remove(current_query)
                await ctx.send(f"Qualifier room `{room_id}` successfully deleted.")

            else:
                await ctx.send(f"Qualifier room `{room_id}` could not found")


    @commands.command(name="qualifier")#maybe rewrite this later, it turned into spagetti a bit
    async def join_rooms(self, ctx, action, room_id=""):
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
            

    @commands.command(name="refRoom")
    @commands.has_role("Referee")
    async def add_referee(self, ctx, room_id):
        """
        A command for referees to take rooms.
        """

        room = db.table("qualifier").get(Query().room_id == room_id)

        if room == None:
            await ctx.send(f"Qualifier room could not find.")  
        elif room["referee"] == ctx.author.name:
            
            db.table("qualifier").update({"referee":None}, Query().room_id == room_id)
            await ctx.send(f"You are removed from room {room_id} as a referee")     
        else:
            
            db.table("qualifier").update({"referee":ctx.author.name}, Query().room_id == room_id)
            await ctx.send(f"You joined to room {room_id} as referee")    

    @commands.command(name="addMpLink")
    @commands.has_role("Referee")
    async def add_mp_link(self, ctx, room_id, mp_link):
        """
        Adds multiplayer match link to the room.
        """

        room = db.table("qualifier").get(Query().room_id == room_id)
        
        if room == None:
            await ctx.send(f"Qualifier room could not find.")
        else:
            
            db.table("qualifier").update({"mp_link":mp_link}, Query().room_id == room_id)
            await ctx.send(f"MP Link added.")

    
    #change into paged embed maybe
    @commands.command(name="rooms")
    async def show_rooms(self, ctx, room_id=""):
        """
        Shows the qualifier rooms.
        
        Either room name for showing a spesific lobby, or day to show lobbies in that day.
        """
        
        days = ["Senin" , "Selasa" , "Rabu" , "Kamis" , "Jumat" , "Sabtu" , "Minggu"]

        if room_id not in days:
            room = db.table("qualifier").get((Query().room_id == room_id) & (Query().guild_id == ctx.guild.id))
            print(room)
            if room != None:
                desc_text = ""
                for player in room["players"]:
                    player_data = db.table("players").get((Query().player_name == player) & (Query().guild_id == ctx.guild.id))
                    
                    desc_text += f"**{player}** - <@{player_data['player_discord_id']}>\n"
                
                embeded = discord.Embed(title = f"**{room['room_id']}** - `{room['day']} {room['time']}` - {room['referee']}" , description=desc_text)

            else:
                await ctx.send(f"No room named {room_id}")
        

        elif room_id in days:

            rooms = db.table("qualifier").search((Query().guild_id == ctx.guild.id) & (Query().day == room_id))
            desc_text = "Name-Day-Time-Referee\n"
            for room in rooms:
            
                desc_text += f"**{room['room_id']}** - `{room['day']} {room['time']}` - {room['referee']}\n"

            embeded = discord.Embed(title = "Qualifier Rooms", description=desc_text)
        await ctx.send(embed=embeded)


    @commands.command(name="bulkAdd")
    @commands.has_permissions(administrator=True)
    async def bulk_add(self, ctx, day ):
        time = 7
        
        table = db.table("qualifier")
        last_lobby_number = int(table.get(doc_id=len(table))["room_id"].split(" ")[1])
        
        for i in range(17):
            
            time = (time + 1)%24
            hour = str(time)
            if len(hour) < 1:
                hour = "0"+hour
            
            things_to_insert = {"room_id":f"Lobby {last_lobby_number+i+1}", "guild_id": ctx.guild.id, "players":[], "day":day, "time":hour+":00", "referee":"", "mp_link":""}
            table.insert(things_to_insert)
        
        await ctx.send(f"Lobbies in {day} has been added")

    @commands.command(name="bulkDelete")
    @commands.has_permissions(administrator=True)
    async def bulk_delete(self, ctx, day ):
        
        db.table("qualifier").remove(Query().day == day)
        await ctx.send(f"Lobbies in {day} has been deleted")

    @commands.command(name="forceAdd")
    @commands.has_permissions(administrator=True)
    async def add_player_by_force(self, ctx, room_id, player_name):

        if room_id == "":
            await ctx.send("no room specified")
            return

        if db.table("qualifier").contains(Query().players.any(player_name)):
            await ctx.send(f"{player_name} is already in a room. To change rooms, use `&forceRemove {player_name}` command first.")
            return

        if not db.table("qualifier").contains(Query().room_id == room_id):
            await ctx.send(f"There is no room called `{room_id}`")
            return

        if not db.table("players").contains(Query().player_name == player_name):
            await ctx.send(f"There is no player called `{player_name}`")
            return

        new_room = db.table("qualifier").get(Query().room_id == room_id)
            
        qualifier_room_size = 16
        if len(new_room["players"]) >= qualifier_room_size:
            await ctx.send("This room is full.")
            return

        new_room["players"].append(player_name)

        db.table("qualifier").update({"players":new_room["players"]},Query().room_id == room_id)
        await ctx.send(f"Player successfull added to room {room_id}")
        
    @commands.command(name="forceRemove")
    @commands.has_permissions(administrator=True)
    async def remove_player_by_force(self, ctx, player_name):
        
        old_room_query = Query().players.any(player_name)

        if db.table("qualifier").contains(old_room_query):

            old_room = db.table("qualifier").get(old_room_query)
            old_room["players"].remove(player_name)
                
            db.table("qualifier").update({"players":old_room["players"]},old_room_query)
            await ctx.send("Player Successfully removed.")
        else:
            await ctx.send("You aren't in any room. Use `&qualifier join` command.")


def setup(bot):
    bot.add_cog(Qualifier(bot))    
