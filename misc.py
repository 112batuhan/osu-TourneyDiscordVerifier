import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

db = TinyDB('db.json')

class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_player(self, ctx, player_name):
        """
        pings a player with their in game name.

        player_name: In game name of the player.
        """
        
        discord_id = db.table("players").get(Query().player_name == player_name)["player_discord_id"]
        await ctx.send(f"{ctx.author.mention} pings <@{discord_id}>")


def setup(bot):
    bot.add_cog(Misc(bot))