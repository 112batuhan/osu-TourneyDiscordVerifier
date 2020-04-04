import os
import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query


client = commands.Bot(command_prefix="&", case_insensitive=True)

cog_list = ["misc", "qualifier", "settings", "verification"]

for cog in cog_list:
    client.load_extension(cog)

@client.event
async def on_ready():
    print(f"Bot Started!!")
    
    
client.run("token")