import discord
import asyncio
import json
import os
from discord.ext import commands

with open('token.txt', 'r') as f:
    token = f.read()

def load_settings():
    global settings
    with open('settings.json', 'r') as f:
        settings = json.load(f)

load_settings()

def is_whitelisted(user):
    if user in settings['whitelist']:
        return True
    else:
        return False

bot = commands.Bot(command_prefix="!")

@bot.command()
async def load(ctx, extension):
    if not is_whitelisted(ctx.author):
        return
    load_settings()
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded {extension}')

@bot.command()
async def unload(ctx, extension):
    if not is_whitelisted(ctx.author):
        return
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Unloaded {extension}')

@bot.command()
async def reload(ctx, extension):
    if not is_whitelisted(ctx.author):
        return
    load_settings()
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Reloaded {extension}')

[bot.load_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if x.endswith('.py') and not x.startswith("_")]

bot.run(token)
