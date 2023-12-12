import discord
from discord.ext import commands


class FileControl(commands.Cog, name="filecontrol"):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(FileControl(bot))
