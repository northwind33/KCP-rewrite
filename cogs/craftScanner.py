import discord
from discord.ext import commands

class CraftScanner(commands.Cog, name="craftScanner"):
    def __init__(self, bot):
        self.bot = bot

        self.partslist = {}
        self.unitslist = {}
        with open("data/partlist.txt", "r") as z:
            for w in z.readlines():
                w = w.split(",")
                partkey = w[0]
                partvalue = w[1:6]
                partvalue[4] = partvalue[4][:-1]
                self.partslist[partkey] = partvalue
        with open("data/unitlist.txt", "r") as a:
            for b in a.readlines():
                b = b.split(",")
                unitkey = b[0]
                unitvalue = float(b[1])
                self.unitslist[unitkey] = unitvalue
        with open("data/season.txt", "r") as c:
            season = c.read().split(",")
            self.seasonversion = season[0]
            self.seasonsize = list(map(float, season[1:4]))
            self.seasonmass = season[4]
            self.seasonpoint = season[5]
            self.seasoncount = season[6]

    @commands.command(name="check", aliases=["검수"])
    async def craft(self, ctx):
        crafts = []
        for x in ctx.message.attachments:
            file = await x.read()
            text = file.decode("utf-8")

            template = {
                'Version': False,
                'Size': False,
                'Part': False,
                'Armor': False,
                'ArmorType': False,
                'Tweak': False,
                'Mass': False,
                'Point': False,
                'Count': False}

            crafts.append([template])

            aicount = 0
            mass = 0
            point = 0
            partcount = 0
            prohibitionpartlist = []
            armorlist = []
            armortypelist = []
            tweaklist = []
            resource = 0
            for x in text.splitlines():
                if "version" in x:
                    version = x[10:]
                    if not version == self.seasonversion:
                        versionerror = 1
                elif "size" in x:
                    sizes = x[7:]
                    sizes = [round(y, 1) for y in map(float, sizes.split(","))]
                    size = " × ".join(map(str, sizes))
                    if sizes[0] > self.seasonsize[0] or sizes[1] > self.seasonsize[1] or sizes[2] > self.seasonsize[2]:
                        sizeerror = 1
                elif "part = " in x:
                    part = x[8:x.find("_")]
                    partcount += 1
                    if part not in self.partslist:
                        prohibitionpartlist.append(part)
                        prohibition = 1
                        parterror = 1
                    else:
                        prohibition = 0
                        partinfo = self.partslist.get(part)
                        if part == "bdPilotAI" or part == "bdShipAI":
                            aicount += 1
                        mass += float(partinfo[0])
                        point += float(partinfo[1])
                elif "modMass" in x and prohibition == 0:
                    modmass = x[11:]
                    mass += float(modmass)
                elif "name = HitpointTracker" in x and prohibition == 0:
                    hitpoint = 1
                elif "Armor = " in x and prohibition == 0 and hitpoint == 1:
                    armor = x[10:]
                    hitpoint = 0
                    if not armor == partinfo[2]:
                        armorlist.append(part)
                        armorerror = 1
                elif "ArmorTypeNum" in x and prohibition == 0:
                    armortype = x[17:]
                    if not armortype == partinfo[3]:
                        armortypelist.append(part)
                        armortypeerror = 1
                elif "currentScale" in x and prohibition == 0:
                    cuttentscale = x[15:]
                elif "defaultScale" in x and prohibition == 0:
                    defaultscale = x[15:]
                    if "u" not in partinfo[4] and cuttentscale > defaultscale:
                        tweaklist.append(part)
                        tweakerror = 1
                elif "RESOURCE" in x and prohibition == 0:
                    resource = 1
                elif "name" in x and resource == 1:
                    unit = x[9:]
                elif "amount" in x and resource == 1:
                    mass += self.unitslist.get(unit) * float(x[11:])
                    resource = 0
            mass = round(mass, 3)
            if mass > int(self.seasonmass):
                masserror = 1
            point = int(point)
            if point > int(self.seasonpoint):
                pointerror = 1
            if partcount > int(self.seasoncount):
                counterror = 1
            if aicount == 0:
                await ctx.send("AI가 없습니다.")
            elif aicount > 1:
                await ctx.send("AI가 2개 이상입니다.")

            print(str(len(ctx.message.attachments)))


def setup(bot):
    bot.add_cog(CraftScanner(bot))
