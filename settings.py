import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

db = TinyDB('db.json')

class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setRegistrationSheet')
    @commands.has_permissions(administrator=True)
    async def set_registration_sheet(self, ctx, sheet_id, worksheet_name, player_range, discord_name_range,check_range):
        """
        Sets the registration sheet.

        sheet_id: ID of the sheet.
        worksheet_name: Name of the sheet in the spreadsheet.
        player_range: Range of the player column in A1 notation.
        discord_name_range: Range of the discord tags column in A1 notation.
        check_range: Range of the checkbox column in A1 notation.

        """


        things_to_update = {"sheet_id": sheet_id, 
                            "worksheet_name": worksheet_name, 
                            "player_range": player_range, 
                            "discord_name_range": discord_name_range,
                            "verify_range":check_range}
        db.table("guilds").update({"verification_sheet_settings": things_to_update}, Query().guild_id == ctx.guild.id)
            
        await ctx.send("Registration sheet has been set.")

    @commands.command(name='setQualifierSheet')
    @commands.has_permissions(administrator=True)
    async def set_qualifier_sheet(self, ctx, sheet_id, worksheet_name, player_range, room_name_range, referee_range, day_range, time_range, match_link_range):
        """
        Sets the qualifier sheet.

        sheet_id: ID of the sheet.
        worksheet_name: Name of the sheet in the spreadsheet.
        ranges: range of the columns in A1 notation.
        """

        things_to_update = {"sheet_id": sheet_id, 
                            "worksheet_name": worksheet_name, 
                            "player_range": player_range, 
                            "room_name_range": room_name_range,
                            "referee_range": referee_range,
                            "day_range": day_range,
                            "time_range": time_range,
                            "match_link_range": match_link_range}
        db.table("guilds").update({"qualifier_sheet_settings": things_to_update}, Query().guild_id == ctx.guild.id)

        await ctx.send("Qualifier sheet has been set.")

    @commands.command(name='setBotChannel')
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx):
        """
        Sets the bot channel and limits certain commands there.
        """

        db.table("guilds").update({"bot_channel":ctx.message.channel.id}, Query().guild_id == ctx.guild.id)
        await ctx.send(f"{str(ctx.message.channel)}has been set.")


    @commands.command(name='resetPlayers')
    @commands.has_permissions(administrator=True)
    async def reset_players(self,ctx):
        """
        Resets the player table
        """

        db.purge_table("players")
        await ctx.send("Players has been deleted.")

    @commands.command(name='init')
    @commands.has_permissions(administrator=True)
    async def initialize_server(self,ctx):
        """
        initializes the database for the server after reseting/deleting it.
        """
        if db.table("guilds").contains(Query().guild_id == ctx.guild.id):
            await ctx.send(f"I'm already initiated here.")
        else:

            things_to_insert = {"guild_id": ctx.guild.id, "qualifier_sheet_settings":None, "verification_sheet_settings":None,  "bot_channel":None }
            db.table("guilds").insert(things_to_insert)

            await ctx.send(f"Initiated in the server")


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        
        if db.table("guilds").contains(Query().guild_id == guild.id):
            print(f"i joined an old server called {guild.name}")
        else:

            things_to_insert = {"guild_id": guild.id, "qualifier_sheet_settings":None, "verification_sheet_settings":None,  "bot_channel":None }
            db.table("guilds").insert(things_to_insert)

            print(f"I joined {guild.name} for the first time!")




#not in use rn
def check_bot_channel(func):
    async def wrapper_check_bot_channel(self, ctx, *args,**kwargs):

        current_guild = db.table("guilds").get(Query().guild_id == ctx.guild.id)
        if current_guild["bot_channel"] == None:
            await ctx.send("Bot channel hasn't been set yet. Use `&setBotChannel` command in the channel you want to be set.")
        elif ctx.message.channel.id == current_guild["bot_channel"]:
            await func(ctx, *args, **kwargs)
        else:
            correct_channel = discord.utils.get(ctx.guild.channels, id=current_guild["bot_channel"])
            await ctx.send(f"Wrong Channel, use {correct_channel.mention}")
        return wrapper_check_bot_channel


def setup(bot):
    bot.add_cog(Settings(bot))