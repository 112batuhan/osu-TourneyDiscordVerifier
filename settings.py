import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

db = TinyDB('db.json')

class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setSheet')
    async def set_sheet(self, ctx, sheet_id, worksheet_name, player_range, discord_name_range,check_range):
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

    @commands.command(name='setBotChannel')
    async def set_channel(self, ctx):
        """
        Sets the bot channel and limits certain commands there.
        """

        db.table("guilds").update({"bot_channel":ctx.message.channel.id}, Query().guild_id == ctx.guild.id)
        await ctx.send(f"{str(ctx.message.channel)}has been set.")


    @commands.command(name='resetPlayers')
    async def reset_players(self,ctx):
        """
        Resets the player table
        """

        db.purge_table("players")
        await ctx.send("Players has been deleted.")


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        
        if db.table("guilds").contains(Query().guild_id == guild.id):
            print(f"i joined an old server called {guild.name}")
        else:
            things_to_insert = {"guild_id": guild.id, "sheet_id": None, "worksheet_name": None, "player_range": None, "discord_name_range":None, "verify_range":None, "bot_channel":None }
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