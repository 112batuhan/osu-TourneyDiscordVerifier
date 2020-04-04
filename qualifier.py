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
            sheet.set_qualifier_settings(**qualifier_settings)
        else:
            await ctx.send(f"Qualifier sheet settings unknown. Use `&setQualifierSheet` command first.")
            return

        current_query = ((Query().guild_id == ctx.guild.id) & (Query().room_id == room_id))

        if action == "add":
                
            if db.table("qualifier").contains(current_query):
                await ctx.send(f"There is already a room with the same id.")
            else:
                sheet.create_room(room_id, day, time)
                things_to_insert = {"room_id":room_id, "guild_id": ctx.guild.id, "players":[], "day":day, "time":time, "referee":None, "mp_link":None}
                db.table("qualifier").insert(things_to_insert)
                await ctx.send(f"Qualifier room `{room_id}` successfully added.")

        elif action == "remove":

            if db.table("qualifier").contains(current_query):
                
                sheet.delete_room(room_id)
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

        qualifier_settings = db.table("guilds").get(Query().guild_id == ctx.guild.id)["qualifier_sheet_settings"]
        sheet.set_qualifier_settings(**qualifier_settings)

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

            sheet.update_players(room_id ,new_room["players"])

            db.table("qualifier").update({"players":new_room["players"]},Query().room_id == room_id)
            await ctx.send(f"Player successfull added to room {room_id}")

        elif action == "leave":
            
            if db.table("qualifier").contains(old_room_query):

                old_room = db.table("qualifier").get(old_room_query)
                old_room["players"].remove(current_player["player_name"])
                sheet.update_players(old_room["room_id"] ,old_room["players"])
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
        qualifier_settings = db.table("guilds").get(Query().guild_id == ctx.guild.id)["qualifier_sheet_settings"]
        sheet.set_qualifier_settings(**qualifier_settings)

        room = db.table("qualifier").get(Query().room_id == room_id)

        if room == None:
            await ctx.send(f"Qualifier room could not find.")  
        elif room["referee"] == ctx.author.name:
            sheet.remove_referee(room_id)
            db.table("qualifier").update({"referee":None}, Query().room_id == room_id)
            await ctx.send(f"You are removed from room {room_id} as a referee")     
        else:
            sheet.add_referee(room_id, ctx.author.name)
            db.table("qualifier").update({"referee":ctx.author.name}, Query().room_id == room_id)
            await ctx.send(f"You joined to room {room_id} as referee")    

    @commands.command(name="addMpLink")
    @commands.has_role("Referee")
    async def add_mp_link(self, ctx, room_id, mp_link):
        """
        Adds multiplayer match link to the room.
        """
        qualifier_settings = db.table("guilds").get(Query().guild_id == ctx.guild.id)["qualifier_sheet_settings"]
        sheet.set_qualifier_settings(**qualifier_settings)

        room = db.table("qualifier").get(Query().room_id == room_id)
        
        if room == None:
            await ctx.send(f"Qualifier room could not find.")
        else:
            sheet.add_mp_link(room_id, mp_link)
            db.table("qualifier").update({"mp_link":mp_link}, Query().room_id == room_id)
            await ctx.send(f"MP Link added.")

    
    #change into paged embed maybe
    @commands.command(name="qualifierRooms")
    async def show_rooms(self, ctx):
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


def setup(bot):
    bot.add_cog(Qualifier(bot))    
