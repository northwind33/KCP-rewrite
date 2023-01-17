import discord
import asyncio
import json
import os
import sys
import shutil
import stat
import traceback
from discord.ext import commands

with open('token.txt', 'r') as f:
    token = f.read()

settings = {}


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


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

paths_list = [["KCP-rewrite/data", "data"], ["KCP-rewrite/cogs", "cogs"]]  # [옮길 파일 위치, 옮겨질 위치]


@bot.command()
async def restart(ctx):
    try:
        if not is_whitelisted(ctx.author.id):
            return
        await ctx.send('봇이 재시작됩니다.')
        if os.path.exists("KCP-rewrite"):
            shutil.rmtree("KCP-rewrite", onerror=on_rm_error)
        os.system("git clone https://github.com/rainy10/KCP-rewrite")
        for paths in paths_list:
            for (path, dirs, files) in os.walk(paths[0]):
                for file_name in files:
                    if os.path.exists(paths[1] + "/" + file_name):
                        os.remove(paths[1] + "/" + file_name)
                    shutil.move(paths[0] + "/" + file_name, paths[1] + "/" + file_name)
        shutil.rmtree("KCP-rewrite", onerror=on_rm_error)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception:
        error_log = traceback.format_exc(limit=None, chain=True)
        cart = bot.get_user(344384179552780289)
        await cart.send("```" + ("-" * 40) + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")


@bot.command()
async def load(ctx, extension):
    if not is_whitelisted(ctx.author.id):
        return
    load_settings()
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded {extension}')


@bot.command()
async def unload(ctx, extension):
    if not is_whitelisted(ctx.author.id):
        return
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Unloaded {extension}')


@bot.command()
async def reload(ctx, extension):
    if not is_whitelisted(ctx.author.id):
        return
    load_settings()
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Reloaded {extension}')


[bot.load_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if
 x.endswith('.py') and not x.startswith("_")]

bot.run(token)
