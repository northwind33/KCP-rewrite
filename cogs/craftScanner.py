import discord
from discord.ext import commands
from decimal import Decimal
import traceback


def up(something):
    if str(something).split(".")[1][:3] == str(round(something, 3)).split(".")[1]:
        return round(something, 3) + Decimal(0.001)
    else:
        return round(something, 3)


def to_str(dec):
    dec = str(dec)
    dec_divide = dec.split(".")
    dec_merge = dec_divide[0] + "." + dec_divide[1][:3]
    return dec_merge


def is_basic_avatar(avatar_url):
    if avatar_url is None:
        return "https://cdn.discordapp.com/attachments/681058514797461647/1064418671100956682/image.png"
    else:
        return avatar_url


def length_limit(dict):
    for key, value in dict.items():
        if len(str(value)) > 500:
            dict[key] = value[:500] + "..."
        else:
            pass
    return dict


class CraftScanner(commands.Cog, name="craftScanner"):
    def __init__(self, bot):
        self.bot = bot
        self.partslist = {}
        self.unitslist = {}
        self.parts_dic = {}
        self.units_dic = {}
        with open("data/partlist.txt", "r") as part:
            for part_div in part.readlines():
                part_div = part_div.split(",")
                partkey = part_div[0]
                part_value = part_div[1:6]
                part_value[4] = part_value[4][:-1]
                self.parts_dic[partkey] = part_value
        with open("data/unitlist.txt", "r") as unit:
            for dic_unit in unit.readlines():
                dic_unit = dic_unit.split(",")
                unitkey = dic_unit[0]
                unitvalue = dic_unit[1][:-1]
                self.units_dic[unitkey] = unitvalue
        with open("data/season.txt", "r") as season_info:
            season = season_info.read().split(",")
            self.seasonversion = season[0]
            self.seasonsize = list(map(float, season[1:4]))
            self.seasonmass = season[4]
            self.seasonpoint = season[5]
            self.seasoncount = season[6]

    @commands.command(name="검수")
    async def craft(self, ctx):
        try:
            crafts = []
            for x in ctx.message.attachments:
                file = await x.read()
                text = file.decode("utf-8")

                template1 = {
                    'Version_pass': False,
                    'Size_pass': False,
                    'Part_pass': False,
                    'Unknown_unit_pass': False,
                    'ArmorType_pass': False,
                    'HullType_pass': False,
                    'Tweak_pass': False,
                    'Mass_pass': False,
                    'Point_pass': False,
                    'Count_pass': False,
                    'AI_pass': False}
                # crafts[-1][2]로 넣어도 자꾸 crafts[-1][0]이 오염되길레 그냥 분리시켜버림
                template2 = {
                    'Version': "",
                    'Size': "",
                    'Part': "",
                    'Unknown_unit': "",
                    'ArmorType': "",
                    'HullType': "",
                    'Tweak': "",
                    'Mass': "",
                    'Point': "",
                    'Count': "",
                    'AI': ""}

                crafts.append([template1, None, template2])

                aicount = 0
                mass = Decimal(0)
                point = 0
                partcount = 0
                prohibitionpartlist = []
                armortypelist = []
                HullTypeList = []
                tweaklist = []
                unknown_unit_list = []
                resource = 0
                for x in text.splitlines():
                    if "ship" in x:
                        name = x[7:]
                        crafts[-1][1] = name
                    elif "version" in x:
                        version = x[10:]
                        if version == self.seasonversion:
                            crafts[-1][0]['Version_pass'] = True
                        crafts[-1][2]['Version'] = version
                    elif "size" in x:
                        sizes = x[7:]
                        sizes = [round(y, 1) for y in map(float, sizes.split(","))]
                        size = " × ".join(map(str, sizes))  # sizes는 [너비, 높이, 길이], size는 ×로 연결한 str
                        if not sizes[0] > self.seasonsize[0] or sizes[1] > self.seasonsize[1] or sizes[2] > self.seasonsize[2]:
                            crafts[-1][0]['Size_pass'] = True
                        crafts[-1][2]['Size'] = size
                    elif "part = " in x:
                        part = x[8:x.rfind("_")]
                        partcount += 1
                        if part not in self.parts_dic:
                            prohibitionpartlist.append(part)
                            prohibition = 1
                        else:
                            prohibition = 0
                            partinfo = self.parts_dic.get(part)
                            if part == "bdPilotAI" or part == "bdShipAI" or part == "bdVTOLAI":
                                aicount += 1
                            mass += Decimal(partinfo[0])
                            point += int(partinfo[1])
                    elif "modMass" in x and prohibition == 0:
                        modmass = x[11:]
                        mass += Decimal(modmass)
                    elif "ArmorTypeNum" in x and prohibition == 0:
                        armortype = x[17:]
                        if not armortype == partinfo[2]:
                            armortypelist.append(part)
                    elif "HullTypeNum" in x and prohibition == 0:
                        HullType = x[16:]
                        if not HullType == partinfo[3]:
                            HullTypeList.append(part)
                    elif "currentScale" in x and prohibition == 0:
                        cuttentscale = x[15:]
                    elif "defaultScale" in x and prohibition == 0:
                        defaultscale = x[15:]
                        if "u" not in partinfo[4] and cuttentscale > defaultscale:
                            tweaklist.append(part)
                    elif "RESOURCE" in x and prohibition == 0:
                        resource = 1
                    elif "name" in x and resource == 1:
                        unit = x[9:]
                    elif "amount" in x and resource == 1:
                        if self.units_dic.get(unit) is None:
                            unknown_unit_list.append(unit)
                        else:
                            mass += Decimal(self.units_dic.get(unit)) * Decimal(x[11:])
                        resource = 0
                if len(prohibitionpartlist) == 0:  # 버젼, 사이즈는 위의 코드에서 처리
                    crafts[-1][0]['Part_pass'] = True
                crafts[-1][2]['Part'] = ", ".join(map(str, prohibitionpartlist))
                if len(unknown_unit_list) == 0:
                    crafts[-1][0]['Unknown_unit_pass'] = True
                crafts[-1][2]['Unknown_unit'] = ", ".join(map(str, unknown_unit_list))
                if len(armortypelist) == 0:
                    crafts[-1][0]['ArmorType_pass'] = True
                crafts[-1][2]['ArmorType'] = ", ".join(map(str, armortypelist))
                if len(HullTypeList) == 0:
                    crafts[-1][0]['HullType_pass'] = True
                crafts[-1][2]['HullType'] = ", ".join(map(str, HullTypeList))
                if len(tweaklist) == 0:
                    crafts[-1][0]['Tweak_pass'] = True
                crafts[-1][2]['Tweak'] = ", ".join(map(str, tweaklist))
                mass = up(mass)  # 무게 소숫점 넷째자리에서 올림
                if mass <= Decimal(self.seasonmass):
                    crafts[-1][0]['Mass_pass'] = True
                crafts[-1][2]['Mass'] = to_str(mass)    # 부동소숫점 오류 제거
                point = int(point)
                if point <= int(self.seasonpoint):
                    crafts[-1][0]['Point_pass'] = True
                crafts[-1][2]['Point'] = point
                if partcount <= int(self.seasoncount):
                    crafts[-1][0]['Count_pass'] = True
                crafts[-1][2]['Count'] = partcount
                if aicount == 1:
                    crafts[-1][0]['AI_pass'] = True
                crafts[-1][2]['AI'] = aicount
            print(crafts)

            author_avatar = is_basic_avatar(ctx.author.avatar)
            if len(crafts) == 0:
                embed = discord.Embed(title="ERROR", description="앗! 확인할 파일이 없어요.\n명령어 입력시 `.craft` 파일을 같이 첨부해주세요.", color=0xeb4258)
                embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                embed.set_thumbnail(url=author_avatar)
                for x in crafts:
                    if x[1] is not None:
                        embed.add_field(name=x[1], value="\n".join(list(map(str, x[0].values()))), inline=False)
                embed.set_footer(text="버그 제보 : cart324#7199")
                await ctx.send(embed=embed)
            else:
                for craft in crafts:
                    passed = True
                    for key, value in craft[0].items():
                        if value == False:
                            passed = False
                            break
                    craft[2] = length_limit(craft[2])
                    if passed:
                        embed = discord.Embed(title=f"'{craft[1]}' 검수 결과", color=0x00ff95)
                        embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                        embed.set_thumbnail(url=author_avatar)
                        embed.add_field(name='버전', value="🟢 " + str(craft[2]['Version']) + ' 버전 사용 기체에요.', inline=False)
                        embed.add_field(name='크기', value="🟢 " + str(craft[2]['Size']), inline=True)
                        embed.add_field(name='부품', value="🟢 " + '와!\n금지된 부품이 발견되지 않았어요.', inline=False)
                        embed.add_field(name='장갑 재질', value="🟢 " + '정상이에요.', inline=False)
                        embed.add_field(name='동체 재질', value="🟢 " + '정상이에요.', inline=False)
                        embed.add_field(name='트윅스케일', value="🟢 " + '정상이에요.', inline=False)
                        embed.add_field(name='무게', value="🟢 " + str(craft[2]['Mass']) + '톤', inline=False)
                        embed.add_field(name='점수', value="🟢 " + str(craft[2]['Point']) + '점', inline=False)
                        embed.add_field(name='파츠수', value="🟢 " + str(craft[2]['Count']) + '개', inline=False)
                        embed.add_field(name='AI', value="🟢 " + '정상이에요.', inline=False)
                        embed.set_footer(text="버그 제보 : cart324#7199")
                        await ctx.send(embed=embed)
                        if ctx.guild:
                            await ctx.message.delete()
                    else:
                        embed = discord.Embed(title=f"'{craft[1]}' 검수 결과", color=0xeb4258)
                        embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                        embed.set_thumbnail(url=author_avatar)
                        if (craft[0]['Version_pass'] == False):
                            embed.add_field(name='버전', value="❌ " + str(craft[2]['Version']) + ' 버전 사용 기체에요.', inline=False)
                        else:
                            embed.add_field(name='버전', value="🟢 " + str(craft[2]['Version']) + ' 버전 사용 기체에요.', inline=False)
                        if (craft[0]['Size_pass'] == False):
                            embed.add_field(name='크기', value="❌ " + str(craft[2]['Size']), inline=False)
                        else:
                            embed.add_field(name='크기', value="🟢 " + str(craft[2]['Size']), inline=False)
                        if (craft[0]['Part_pass'] == False):
                            embed.add_field(name='부품', value="❌ " + str(craft[2]['Part']), inline=False)
                        else:
                            embed.add_field(name='부품', value="🟢 " + '와!\n금지된 부품이 발견되지 않았어요.', inline=False)
                        if (craft[0]['Unknown_unit_pass'] == False):
                            embed.add_field(name='❗ 알 수 없는 자원이 발견되었어요.', value=str(craft[2]['Unknown_unit']))
                        if (craft[0]['ArmorType_pass'] == False):
                            embed.add_field(name='장갑 재질', value="❌ " + str(craft[2]['ArmorType']), inline=False)
                        else:
                            embed.add_field(name='장갑 재질', value="🟢 " + '정상이에요.', inline=False)
                        if (craft[0]['HullType_pass'] == False):
                            embed.add_field(name='동체 재질', value="❌ " + str(craft[2]['HullType']), inline=False)
                        else:
                            embed.add_field(name='동체 재질', value="🟢 " + '정상이에요.', inline=False)
                        if (craft[0]['Tweak_pass'] == False):
                            embed.add_field(name='트윅스케일', value="❌ " + '금지된 트윅스케일이 사용되었어요.\n' + str(craft[2]['Tweak']),
                                            inline=False)
                        else:
                            embed.add_field(name='트윅스케일', value="🟢 " + '정상이에요.', inline=False)
                        if (craft[0]['Mass_pass'] == False):
                            embed.add_field(name='무게', value="❌ " + str(craft[2]['Mass']) + '톤', inline=False)
                        else:
                            embed.add_field(name='무게', value="🟢 " + str(craft[2]['Mass']) + '톤', inline=False)
                        if (craft[0]['Point_pass'] == False):
                            embed.add_field(name='점수', value="❌ " + str(craft[2]['Point']) + '점', inline=False)
                        else:
                            embed.add_field(name='점수', value="🟢 " + str(craft[2]['Point']) + '점', inline=False)
                        if (craft[0]['Count_pass'] == False):
                            embed.add_field(name='파츠수', value="❌ " + str(craft[2]['Count']) + '개', inline=False)
                        else:
                            embed.add_field(name='파츠수', value="🟢 " + str(craft[2]['Count']) + '개', inline=False)
                        if (craft[0]['AI_pass'] == False):
                            embed.add_field(name='AI', value="❌ " + str(craft[2]['AI']) + '개', inline=False)
                        else:
                            embed.add_field(name='AI', value="🟢 " + '정상이에요.', inline=False)
                        embed.set_footer(text="버그 제보 : cart324#7199")
                        await ctx.send(embed=embed)
                        if ctx.guild:
                            await ctx.message.delete()
        except Exception:
            embed = discord.Embed(title="ERROR", color=0xeb4258)
            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
            embed.set_thumbnail(url=author_avatar)
            embed.add_field(name='감각이 없으니 이게 어떻게 된일이요?', value='어... 하필이면 오류가 영 좋지 않은 곳에 발생했어요.', inline=False)
            embed.add_field(name='내가 버그라니!', value='오류는 자동으로 전달되었으니 문제가 해결될 때 까지 기다려주세요.', inline=False)
            await ctx.send(embed=embed)
            error_log = traceback.format_exc(limit=None, chain=True)
            cart = self.bot.get_user(344384179552780289)
            await cart.send(("-" * 40) + "\n" + "사용자 = " + ctx.author.name + "\n" + str(error_log))


# 영어(복붙)

    @commands.command(name="check")
    async def craft_EN(self, ctx):
        try:
            crafts = []
            for x in ctx.message.attachments:
                file = await x.read()
                text = file.decode("utf-8")

                template1 = {
                    'Version_pass': False,
                    'Size_pass': False,
                    'Part_pass': False,
                    'Unknown_unit_pass': False,
                    'ArmorType_pass': False,
                    'HullType_pass': False,
                    'Tweak_pass': False,
                    'Mass_pass': False,
                    'Point_pass': False,
                    'Count_pass': False,
                    'AI_pass': False}
                # crafts[-1][2]로 넣어도 자꾸 crafts[-1][0]이 오염되길레 그냥 분리시켜버림
                template2 = {
                    'Version': "",
                    'Size': "",
                    'Part': "",
                    'Unknown_unit': "",
                    'ArmorType': "",
                    'HullType': "",
                    'Tweak': "",
                    'Mass': "",
                    'Point': "",
                    'Count': "",
                    'AI': ""}

                crafts.append([template1, None, template2])

                aicount = 0
                mass = Decimal(0)
                point = 0
                partcount = 0
                prohibitionpartlist = []
                armortypelist = []
                HullTypeList = []
                tweaklist = []
                unknown_unit_list = []
                resource = 0
                for x in text.splitlines():
                    if "ship" in x:
                        name = x[7:]
                        crafts[-1][1] = name
                    elif "version" in x:
                        version = x[10:]
                        if version == self.seasonversion:
                            crafts[-1][0]['Version_pass'] = True
                        crafts[-1][2]['Version'] = version
                    elif "size" in x:
                        sizes = x[7:]
                        sizes = [round(y, 1) for y in map(float, sizes.split(","))]
                        size = " × ".join(map(str, sizes))  # sizes는 [너비, 높이, 길이], size는 ×로 연결한 str
                        if not sizes[0] > self.seasonsize[0] or sizes[1] > self.seasonsize[1] or sizes[2] > self.seasonsize[2]:
                            crafts[-1][0]['Size_pass'] = True
                        crafts[-1][2]['Size'] = size
                    elif "part = " in x:
                        part = x[8:x.rfind("_")]
                        partcount += 1
                        if part not in self.parts_dic:
                            prohibitionpartlist.append(part)
                            prohibition = 1
                        else:
                            prohibition = 0
                            partinfo = self.parts_dic.get(part)
                            if part == "bdPilotAI" or part == "bdShipAI" or part == "bdVTOLAI":
                                aicount += 1
                            mass += Decimal(partinfo[0])
                            point += int(partinfo[1])
                    elif "modMass" in x and prohibition == 0:
                        modmass = x[11:]
                        mass += Decimal(modmass)
                    elif "ArmorTypeNum" in x and prohibition == 0:
                        armortype = x[17:]
                        if not armortype == partinfo[2]:
                            armortypelist.append(part)
                    elif "HullTypeNum" in x and prohibition == 0:
                        HullType = x[16:]
                        if not HullType == partinfo[3]:
                            HullTypeList.append(part)
                    elif "currentScale" in x and prohibition == 0:
                        cuttentscale = x[15:]
                    elif "defaultScale" in x and prohibition == 0:
                        defaultscale = x[15:]
                        if "u" not in partinfo[4] and cuttentscale > defaultscale:
                            tweaklist.append(part)
                    elif "RESOURCE" in x and prohibition == 0:
                        resource = 1
                    elif "name" in x and resource == 1:
                        unit = x[9:]
                    elif "amount" in x and resource == 1:
                        if self.units_dic.get(unit) is None:
                            unknown_unit_list.append(unit)
                        else:
                            mass += Decimal(self.units_dic.get(unit)) * Decimal(x[11:])
                        resource = 0
                if len(prohibitionpartlist) == 0:  # 버젼, 사이즈는 위의 코드에서 처리
                    crafts[-1][0]['Part_pass'] = True
                crafts[-1][2]['Part'] = ", ".join(map(str, prohibitionpartlist))
                if len(unknown_unit_list) == 0:
                    crafts[-1][0]['Unknown_unit_pass'] = True
                crafts[-1][2]['Unknown_unit'] = ", ".join(map(str, unknown_unit_list))
                if len(armortypelist) == 0:
                    crafts[-1][0]['ArmorType_pass'] = True
                crafts[-1][2]['ArmorType'] = ", ".join(map(str, armortypelist))
                if len(HullTypeList) == 0:
                    crafts[-1][0]['HullType_pass'] = True
                crafts[-1][2]['HullType'] = ", ".join(map(str, HullTypeList))
                if len(tweaklist) == 0:
                    crafts[-1][0]['Tweak_pass'] = True
                crafts[-1][2]['Tweak'] = ", ".join(map(str, tweaklist))
                mass = up(mass)  # 무게 소숫점 넷째자리에서 올림
                if mass <= Decimal(self.seasonmass):
                    crafts[-1][0]['Mass_pass'] = True
                crafts[-1][2]['Mass'] = to_str(mass)    # 부동소숫점 오류 제거
                point = int(point)
                if point <= int(self.seasonpoint):
                    crafts[-1][0]['Point_pass'] = True
                crafts[-1][2]['Point'] = point
                if partcount <= int(self.seasoncount):
                    crafts[-1][0]['Count_pass'] = True
                crafts[-1][2]['Count'] = partcount
                if aicount == 1:
                    crafts[-1][0]['AI_pass'] = True
                crafts[-1][2]['AI'] = aicount
            print(crafts)

            author_avatar = is_basic_avatar(ctx.author.avatar)
            if len(crafts) == 0:
                embed = discord.Embed(title="ERROR", description="OOPS, The file is missing.\n Please attach your `.craft` file when using this command.", color=0xeb4258)
                embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                embed.set_thumbnail(url=author_avatar)
                for x in crafts:
                    if x[1] is not None:
                        embed.add_field(name=x[1], value="\n".join(list(map(str, x[0].values()))), inline=False)
                embed.set_footer(text="Bug report : cart324#7199")
                await ctx.send(embed=embed)
            else:
                for craft in crafts:
                    passed = True
                    for key, value in craft[0].items():
                        if value == False:
                            passed = False
                            break
                    craft[2] = length_limit(craft[2])
                    if passed:
                        embed = discord.Embed(title=f"'{craft[1]}' Results", color=0x00ff95)
                        embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                        embed.set_thumbnail(url=author_avatar)
                        embed.add_field(name='Game Version', value="🟢 " + str(craft[2]['Version']), inline=False)
                        embed.add_field(name='Dimensions', value="🟢 " + str(craft[2]['Size']), inline=True)
                        embed.add_field(name='Forbidden Parts', value="🟢 " + 'Hooray!\nBanned parts not found', inline=False)
                        embed.add_field(name='Armor Type', value="🟢 " + 'OK', inline=False)
                        embed.add_field(name='Hull Material', value="🟢 " + 'OK', inline=False)
                        embed.add_field(name='Tweakscale on Improper Parts', value="🟢 " + 'OK', inline=False)
                        embed.add_field(name='Mass', value="🟢 " + str(craft[2]['Mass']) + 't', inline=False)
                        embed.add_field(name='Points', value="🟢 " + str(craft[2]['Point']) + 'Pt(s)', inline=False)
                        embed.add_field(name='Parts Count', value="🟢 " + str(craft[2]['Count']), inline=False)
                        embed.add_field(name='AI', value="🟢 " + 'OK', inline=False)
                        embed.set_footer(text="Bug report : cart324#7199")
                        await ctx.send(embed=embed)
                        if ctx.guild:
                            await ctx.message.delete()
                    else:
                        embed = discord.Embed(title=f"'{craft[1]}' Results", color=0xeb4258)
                        embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                        embed.set_thumbnail(url=author_avatar)
                        if (craft[0]['Version_pass'] == False):
                            embed.add_field(name='Game Version', value="❌ " + str(craft[2]['Version']), inline=False)
                        else:
                            embed.add_field(name='Game Version', value="🟢 " + str(craft[2]['Version']), inline=False)
                        if (craft[0]['Size_pass'] == False):
                            embed.add_field(name='Dimensions', value="❌ " + str(craft[2]['Size']), inline=False)
                        else:
                            embed.add_field(name='Dimensions', value="🟢 " + str(craft[2]['Size']), inline=False)
                        if (craft[0]['Part_pass'] == False):
                            embed.add_field(name='Forbidden Parts', value="❌ " + str(craft[2]['Part']), inline=False)
                        else:
                            embed.add_field(name='Forbidden Parts', value="🟢 " + 'Hooray!\nBanned parts not found', inline=False)
                        if (craft[0]['Unknown_unit_pass'] == False):
                            embed.add_field(name='❗ Unknown Unit Detected', value=str(craft[2]['Unknown_unit']))
                        if (craft[0]['ArmorType_pass'] == False):
                            embed.add_field(name='Armor Type', value="❌ " + str(craft[2]['ArmorType']), inline=False)
                        else:
                            embed.add_field(name='Armor Type', value="🟢 " + 'OK', inline=False)
                        if (craft[0]['HullType_pass'] == False):
                            embed.add_field(name='Hull Material', value="❌ " + str(craft[2]['HullType']), inline=False)
                        else:
                            embed.add_field(name='Hull Material', value="🟢 " + 'OK', inline=False)
                        if (craft[0]['Tweak_pass'] == False):
                            embed.add_field(name='Tweakscale on Improper Parts', value="❌ " + 'Inappropriate use of TweakScale detected\n' + str(craft[2]['Tweak']),
                                            inline=False)
                        else:
                            embed.add_field(name='Tweakscale on Improper Parts', value="🟢 " + 'OK', inline=False)
                        if (craft[0]['Mass_pass'] == False):
                            embed.add_field(name='Mass', value="❌ " + str(craft[2]['Mass']) + 't', inline=False)
                        else:
                            embed.add_field(name='Mass', value="🟢 " + str(craft[2]['Mass']) + 't', inline=False)
                        if (craft[0]['Point_pass'] == False):
                            embed.add_field(name='Points', value="❌ " + str(craft[2]['Point']) + 'Pt(s)', inline=False)
                        else:
                            embed.add_field(name='Points', value="🟢 " + str(craft[2]['Point']) + 'Pt(s)', inline=False)
                        if (craft[0]['Count_pass'] == False):
                            embed.add_field(name='Parts Count', value="❌ " + str(craft[2]['Count']), inline=False)
                        else:
                            embed.add_field(name='Parts Count', value="🟢 " + str(craft[2]['Count']), inline=False)
                        if (craft[0]['AI_pass'] == False):
                            embed.add_field(name='AI', value="❌ " + "Too many AIs", inline=False)
                        else:
                            embed.add_field(name='AI', value="🟢 " + 'OK', inline=False)
                        embed.set_footer(text="Bug report : cart324#7199")
                        await ctx.send(embed=embed)
                        if ctx.guild:
                            await ctx.message.delete()
        except Exception:
            embed = discord.Embed(title="ERROR", color=0xeb4258)
            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
            embed.set_thumbnail(url=author_avatar)
            embed.add_field(name='This has been the worst bug in the history of bugs, maybe ever.', value='​', inline=False)
            embed.add_field(name='Apply cold water to the bugged area.', value="Achthually, you don't need to. The automatic report is on the way.", inline=False)
            await ctx.send(embed=embed)
            error_log = traceback.format_exc(limit=None, chain=True)
            cart = self.bot.get_user(344384179552780289)
            await cart.send(("-" * 40) + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log))

def setup(bot):
    bot.add_cog(CraftScanner(bot))
