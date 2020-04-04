import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

from spreadsheet import Sheet

sheet = Sheet("osutournamentdiscordjoincheck-84f8d6e67c81.json")
db = TinyDB('db.json')

class Verification(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

        
    @commands.command(name='addVerifiedPlayers')
    async def add_players_in_bulk(self,ctx):
        """
        Adds verified players into the database from sheet
        """

        server_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
        verified_player_data = sheet.get_player_list(**server_info["verification_sheet_settings"])

        none_list = []

        for player in verified_player_data:
            
            discord_name, discord_tag = player[1].split("#")
            discord_user = discord.utils.get(ctx.guild.members, name=discord_name, discriminator=discord_tag)

            if discord_user == None:
                none_list.append(f"`{player[0]}` | `{player[1]}`")
            else:
                things_to_upsert = {"player_name":player[0], "player_discord_id": discord_user.id, "guild_id": ctx.guild.id}
                db.table("players").upsert(things_to_upsert , (Query().player_discord_id == discord_user.id) & (Query().guild_id == ctx.guild.id))
        
        await ctx.send(f"{len(verified_player_data) - len(none_list)} players are added.")

        if len(none_list)>0:
            await ctx.send(f"These players couldn't be find in the server:\n"+ "\n".join(none_list) +" \nThey might have changed their discord information after signing up.")
        


    @commands.command(name='verify')
    async def set_player(self, ctx, player_name):
        """
        Verifies a player in the sheet.

        player_name: Players in game name.
        """

        discord_user = discord.utils.get(ctx.guild.members, id=ctx.author.id)
        
        try:

            server_info = db.table("guilds").get(Query().guild_id == ctx.guild.id)
            sheet.update_player(player_name, str(discord_user), **server_info["verification_sheet_settings"])

            things_to_upsert = {"player_name":player_name, "player_discord_id": ctx.author.id, "guild_id": ctx.guild.id}
            db.table("players").upsert(things_to_upsert , (Query().player_discord_id == ctx.author.id) & (Query().guild_id == ctx.guild.id))

            await ctx.send("Player successfully verified!")

        except KeyError:
            await ctx.send(f"Player not found in the sheet.")


def setup(bot):
    bot.add_cog(Verification(bot))