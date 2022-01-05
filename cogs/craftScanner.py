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

    @commands.command(name="검수")
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
                'Count': False,
                'AI': False}

            crafts.append([template, None])

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
                if "ship" in x:
                    name = x[7:]
                    crafts[-1][1] = name
                elif "version" in x:
                    version = x[10:]
                    if not version == self.seasonversion:
                        crafts[-1][0]['Version'] = version
                elif "size" in x:
                    sizes = x[7:]
                    sizes = [round(y, 1) for y in map(float, sizes.split(","))]
                    size = " × ".join(map(str, sizes))
                    if sizes[0] > self.seasonsize[0] or sizes[1] > self.seasonsize[1] or sizes[2] > self.seasonsize[2]:
                        crafts[-1][0]['Size'] = size
                elif "part = " in x:
                    part = x[8:x.rfind("_")]
                    partcount += 1
                    if part not in self.partslist:
                        prohibitionpartlist.append(part)
                        prohibition = 1
                        crafts[-1][0]['Part'] = part
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
                        crafts[-1][0]['Armor'] = armor
                elif "ArmorTypeNum" in x and prohibition == 0:
                    armortype = x[17:]
                    if not armortype == partinfo[3]:
                        armortypelist.append(part)
                        crafts[-1][0]['ArmorType'] = armortype
                elif "currentScale" in x and prohibition == 0:
                    cuttentscale = x[15:]
                elif "defaultScale" in x and prohibition == 0:
                    defaultscale = x[15:]
                    if "u" not in partinfo[4] and cuttentscale > defaultscale:
                        tweaklist.append(part)
                        crafts[-1][0]['Tweak'] = True
                elif "RESOURCE" in x and prohibition == 0:
                    resource = 1
                elif "name" in x and resource == 1:
                    unit = x[9:]
                elif "amount" in x and resource == 1:
                    mass += self.unitslist.get(unit) * float(x[11:])
                    resource = 0
            mass = round(mass, 3)
            if mass > float(self.seasonmass):
                crafts[-1][0]['Mass'] = mass
            point = int(point)
            if point > int(self.seasonpoint):
                crafts[-1][0]['Point'] = point
            if partcount > int(self.seasoncount):
                crafts[-1][0]['Part'] = partcount
            if aicount != 1:
                crafts[-1][0]['AI'] = aicount

        if len(crafts) == 1:
            passed = True
            for key, value in crafts[0][0].items():
                if value is not False:
                    passed = False
                    break
            if passed:
                embed = discord.Embed(title="검수 결과", color=0x00ff95)
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.add_field(name='버전', value="🟢 " + str(crafts[0][0]['Version']), inline=False)
                embed.add_field(name='크기', value="🟢 " + str(crafts[0][0]['Size']), inline=True)
                embed.add_field(name='부품', value="🟢 " + '정상', inline=False)
                embed.add_field(name='장갑', value="🟢 " + '정상', inline=False)
                embed.add_field(name='장갑 재질', value="🟢 " + '정상', inline=False)
                embed.add_field(name='트윅스케일', value="🟢 " + '정상', inline=False)
                embed.add_field(name='무게', value="🟢 " + str(crafts[0][0]['Mass']) + '톤', inline=False)
                embed.add_field(name='점수', value="🟢 " + str(crafts[0][0]['Point']) + '점', inline=False)
                embed.add_field(name='AI', value="🟢 " + '정상', inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="검수 결과", color=0xeb4258)
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                if(crafts[0][0]['Version'] is not False):
                    embed.add_field(name='버전', value="❌ " + str(crafts[0][0]['Version']), inline=False)
                else:
                    embed.add_field(name='버전', value="🟢 " + str(crafts[0][0]['Version']), inline=False)
                if(crafts[0][0]['Size'] is not False):
                    embed.add_field(name='크기', value="❌ " + str(crafts[0][0]['Size']), inline=False)
                else:
                    embed.add_field(name='크기', value="🟢 " + str(crafts[0][0]['Size']), inline=False)
                if(crafts[0][0]['Part'] is not False):
                    embed.add_field(name='부품', value="❌ " + str(crafts[0][0]['Part']), inline=False)
                else:
                    embed.add_field(name='부품', value="🟢 " + '정상', inline=False)
                if(crafts[0][0]['Armor'] is not False):
                    embed.add_field(name='장갑', value="❌ " + str(crafts[0][0]['Armor']), inline=False)
                else:
                    embed.add_field(name='장갑', value="🟢 " + '정상', inline=False)
                if(crafts[0][0]['ArmorType'] is not False):
                    embed.add_field(name='장갑 재질', value="❌ " + str(crafts[0][0]['ArmorType']), inline=False)
                else:
                    embed.add_field(name='장갑 재질', value="🟢 " + '정상', inline=False)
                if(crafts[0][0]['Tweak'] is not False):
                    embed.add_field(name='트윅스케일', value="❌ " + '금지된 트윅스케일 사용됨', inline=False)
                else:
                    embed.add_field(name='트윅스케일', value="🟢 " + '정상', inline=False)
                if(crafts[0][0]['Mass'] is not False):
                    embed.add_field(name='무게', value="❌ " + str(crafts[0][0]['Mass']) + '톤', inline=False)
                else:
                    embed.add_field(name='무게', value="🟢 " + str(crafts[0][0]['Mass']) + '톤', inline=False)
                if(crafts[0][0]['Point'] is not False):
                    embed.add_field(name='점수', value="❌ " + str(crafts[0][0]['Point']) + '점', inline=False)
                else:
                    embed.add_field(name='점수', value="🟢 " + str(crafts[0][0]['Point']) + '점', inline=False)
                if(crafts[0][0]['AI'] is not False):
                    embed.add_field(name='AI', value="❌ " + str(crafts[0][0]['AI']) + '개', inline=False)
                else:
                    embed.add_field(name='AI', value="🟢 " + '정상', inline=False)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="검수 결과", description="대충 뭉치검수 만드는 중", color=0xffffff)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            for x in crafts:
                if x[1] is not None:
                    embed.add_field(name=x[1], value="\n".join(list(map(str, x[0].values()))), inline=False)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CraftScanner(bot))
