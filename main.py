import discord
from discord import ExtensionAlreadyLoaded, ExtensionNotFound, ExtensionNotLoaded
from discord.ext import commands
import os
import shutil
import stat
import traceback
import time


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

current_cogs_list = []

project_name = "KCP-rewrite-main"  # <<<<< 새 봇 제작시 바꿀 것!!


def print_log(text):
    now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
    print(now + text)


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def load_all_cogs():
    global current_cogs_list
    for i in os.listdir("cogs"):
        if i.endswith(".py"):
            client.load_extension(f"cogs.{i.split('.')[0]}")
            current_cogs_list.append(i)


def unload_all_cogs():
    global current_cogs_list
    for i in current_cogs_list:
        client.unload_extension(f"Cogs.{i.split('.')[0]}")
    current_cogs_list = []


# 최초 cog 로딩
load_all_cogs()
print_log(f"bot has been started, loaded cogs : {current_cogs_list}")


@client.slash_command()
async def cog_list(ctx):
    avail_cogs_list = []
    for i in os.listdir("cogs"):
        if i.endswith(".py") and (i not in current_cogs_list):
            avail_cogs_list.append(i)

    await ctx.respond("로드 가능한 cog :" + str(avail_cogs_list) + "\n현제 로드된 cog :" + str(current_cogs_list))


@client.slash_command()
async def unload_cog(ctx, cog_name: discord.Option(str)):
    global current_cogs_list
    try:
        client.unload_extension(f"Cogs.{cog_name}")
        current_cogs_list.remove(f"{cog_name}.py")
        print_log(f"{cog_name} has been unloaded")
        await ctx.respond(f"{cog_name}을 언로드 하였습니다.")

    except ExtensionNotFound:
        await ctx.respond(f"{cog_name}을 찾을 수 없습니다.")

    except ExtensionNotLoaded:
        await ctx.respond(f"{cog_name}은 로드되어 있지 않습니다.")

    except Exception:
        error_log = traceback.format_exc(limit=None, chain=True)
        cart = client.get_user(344384179552780289)
        print_log(f"error has been occurred")
        await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")


@client.slash_command()
async def load_cog(ctx, cog_name: discord.Option(str)):
    global current_cogs_list
    try:
        client.load_extension(f"Cogs.{cog_name}")
        current_cogs_list.append(f"{cog_name}.py")
        print_log(f"{cog_name} has been loaded")
        await ctx.respond(f"{cog_name}을 로드 하였습니다.")

    except ExtensionNotFound:
        await ctx.respond(f"{cog_name}을 찾을 수 없습니다.")

    except ExtensionAlreadyLoaded:
        await ctx.respond(f"{cog_name}은 이미 로드되어 있습니다.")

    except Exception:
        error_log = traceback.format_exc(limit=None, chain=True)
        cart = client.get_user(344384179552780289)
        print_log(f"error has been occurred")
        await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")


@client.slash_command()
async def update(ctx):
    try:
        if os.path.exists(project_name):    # 다운로드 폴더 확인
            shutil.rmtree(project_name, onerror=on_rm_error)

        os.system(f"git clone https://github.com/cart324/{project_name}")

        for i in os.listdir(project_name):

            for (root, dirs, files) in os.walk(f"{project_name}/{i}"):
                for file in files:
                    if os.path.exists(i + "/" + file):
                        os.remove(i + "/" + file)
                    shutil.move(project_name + "/" + i + "/" + file, i + "/" + file)

        shutil.rmtree(project_name, onerror=on_rm_error)

        unload_all_cogs()
        load_all_cogs()

        print_log("update completed")
        await ctx.respond("업데이트가 완료되었습니다.")

    except Exception:
        error_log = traceback.format_exc(limit=None, chain=True)
        cart = client.get_user(344384179552780289)
        print_log(f"error has been occurred")
        await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")


with open('token.txt', 'r') as f:
    token = f.read()


client.run(token)
