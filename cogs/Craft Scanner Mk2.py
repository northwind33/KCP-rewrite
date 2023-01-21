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


def is_passed(pass_dic):
    passed = True
    for value in pass_dic.values():
        if value is False:
            passed = False
            break
    return passed


def length_limit(dic):
    for key, value in dic.items():
        if len(str(value)) > 500:
            dic[key] = value[:500] + "..."
        else:
            pass
    return dic


class CraftScanner(commands.Cog, name="craftScanner"):
    def __init__(self, bot):
        self.bot = bot
        self.parts_dic = {}
        self.units_dic = {}
        with open("data/partlist.txt", "r") as part_data:
            for part in part_data.readlines():
                part_dic = {}
                part = part.split(",")
                part_key = part[0]
                part_dic["part_Mass"] = part[1]
                part_dic["part_Point"] = part[2]
                part_dic["part_ArmorType"] = part[3]
                part_dic["part_HullType"] = part[4]
                part_dic["part_TweakScale"] = part[5][:-1]
                self.parts_dic[part_key] = part_dic
        with open("data/unitlist.txt", "r") as unit_data:
            for unit in unit_data.readlines():
                unit = unit.split(",")
                unit_key = unit[0]
                unit_value = unit[1][:-1]
                self.units_dic[unit_key] = unit_value
        with open("data/season.txt", "r") as season_data:
            season = season_data.read().split(",")
            self.season_version = season[0]
            self.season_size = list(map(float, season[1:4]))
            self.season_mass = season[4]
            self.season_point = season[5]
            self.season_count = season[6]

    def check(self, file):
        template = {
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
        craft = [template, None, {}]

        part_count = 0
        mass = Decimal(0)
        point = int(0)
        prohibition_list = []
        armor_type_list = []
        hull_type_list = []
        tweak_list = []
        unknown_unit_list = []
        ai_count = 0
        prohibition = False
        resource = False

        for line in file.splitlines():
            if "ship" in line:
                name = line[7:]
                craft[1] = name

            elif "version" in line:
                version = line[10:]
                craft[2]['Version'] = version
                if version == self.season_version:
                    craft[0]['Version_pass'] = True

            elif "size" in line:
                sizes = line[7:]
                sizes = [round(y, 1) for y in map(float, sizes.split(","))]
                size = " × ".join(map(str, sizes))  # sizes는 [너비, 높이, 길이], size는 ×로 연결한 str
                craft[2]['Size'] = size
                if not sizes[0] > self.season_size[0] \
                        or sizes[1] > self.season_size[1] \
                        or sizes[2] > self.season_size[2]:
                    craft[0]['Size_pass'] = True

            elif "part = " in line:
                part_name = line[8:line.rfind("_")]
                part_count += 1
                if part_name in self.parts_dic:
                    prohibition = False
                    if part_name == "bdPilotAI" or part_name == "bdShipAI" or part_name == "bdVTOLAI":
                        ai_count += 1
                    part_info = self.parts_dic.get(part_name)
                    mass += Decimal(part_info.get("part_Mass"))
                    point += int(part_info.get("part_Point"))
                else:
                    prohibition = True
                    prohibition_list.append(part_name)

            if prohibition is False:
                if "modMass" in line:
                    modmass = line[11:]
                    mass += Decimal(modmass)

                elif "ArmorTypeNum" in line:
                    armor_type = line[17:]
                    if not armor_type == part_info.get("part_ArmorType"):
                        armor_type_list.append(part_name)

                elif "HullTypeNum" in line:
                    hull_type = line[16:]
                    if not hull_type == part_info.get("part_HullType"):
                        hull_type_list.append(part_name)

                elif "currentScale" in line:
                    current_scale = line[15:]

                elif "defaultScale" in line:
                    default_scale = line[15:]
                    if "u" not in part_info.get("part_TweakScale") and current_scale > default_scale:
                        tweak_list.append(part_name)

                elif "RESOURCE" in line:
                    resource = True

                if resource is True:
                    if "name" in line:
                        unit_name = line[9:]

                    elif "amount" in line:
                        amount = line[11:]
                        if unit_name in self.units_dic:
                            mass += Decimal(self.units_dic.get(unit_name)) * Decimal(amount)
                        else:
                            unknown_unit_list.append(unit_name)
                        resource = False

        if len(prohibition_list) == 0:  # 버젼, 사이즈는 위의 코드에서 처리
            craft[0]['Part_pass'] = True
        craft[2]['Part'] = ", ".join(prohibition_list)

        if len(unknown_unit_list) == 0:
            craft[0]['Unknown_unit_pass'] = True
        craft[2]['Unknown_unit'] = ", ".join(unknown_unit_list)

        if len(armor_type_list) == 0:
            craft[0]['ArmorType_pass'] = True
        craft[2]['ArmorType'] = ", ".join(armor_type_list)

        if len(hull_type_list) == 0:
            craft[0]['HullType_pass'] = True
        craft[2]['HullType'] = ", ".join(hull_type_list)

        if len(tweak_list) == 0:
            craft[0]['Tweak_pass'] = True
        craft[2]['Tweak'] = ", ".join(tweak_list)

        mass = up(mass)  # 무게 소수점 넷째 자리에서 올림
        if mass <= Decimal(self.season_mass):
            craft[0]['Mass_pass'] = True
        craft[2]['Mass'] = to_str(mass)  # 부동소수점 오류 제거

        if point <= int(self.season_point):
            craft[0]['Point_pass'] = True
        craft[2]['Point'] = str(point)

        if part_count <= int(self.season_count):
            craft[0]['Count_pass'] = True
        craft[2]['Count'] = str(part_count)

        if ai_count == 1:
            craft[0]['AI_pass'] = True
        craft[2]['AI'] = str(ai_count)

        return craft

    # [제목, craft[0]키, craft[2]키, 통과시 추가 문구, 비통과시 추가 문구]
    texts_kr = [['버전', 'Version_pass', 'Version', ' 버전 사용 기체에요.', ' 버전 사용 기체에요.'],
                ['파츠수', 'Count_pass', 'Count', '개', '개'],
                ['무게', 'Mass_pass', 'Mass', '톤', '톤'],
                ['크기', 'Size_pass', 'Size', '', ''],
                ['점수', 'Point_pass', 'Point', '점', '점'],
                ['금지 부품', 'Part_pass', 'Part', '와! 금지된 부품이 발견되지 않았어요.', ''],
                ['장갑 재질', 'ArmorType_pass', 'ArmorType', '정상이에요.', ''],
                ['동체 재질', 'HullType_pass', 'HullType', '정상이에요.', ''],
                ['금지된 트윅스케일', 'Tweak_pass', 'Tweak', '정상이에요.', '']]

    @commands.command(name="검수")
    async def craft(self, ctx):
        author_avatar = is_basic_avatar(ctx.author.avatar)
        try:
            crafts = []
            ext_error = False
            for file in ctx.message.attachments:
                if str(file).split(".")[-1] == "craft":
                    file = await file.read()
                    file = file.decode("utf-8")
                    crafts.append(self.check(file))  # 파일 검수
                else:
                    ext_error = True
                    embed = discord.Embed(title="ERROR",
                                          description="앗! 알 수 없는 파일이에요.\n`.craft` 파일만을 첨부해 주세요.",
                                          color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="버그 제보 : cart324#7199")
                    await ctx.send(embed=embed)

            if len(crafts) == 0:
                if ext_error:
                    pass
                else:
                    embed = discord.Embed(title="ERROR",
                                          description="앗! 확인할 파일이 없어요.\n명령어 입력 시 `.craft` 파일을 같이 첨부해 주세요.",
                                          color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="버그 제보 : cart324#7199")
                    await ctx.send(embed=embed)
            else:
                for craft in crafts:
                    craft[2] = length_limit(craft[2])
                    passed = is_passed(craft[0])
                    if passed:
                        embed = discord.Embed(title=f"'{craft[1]}' 검수 결과", color=0x00ff95)
                    else:
                        embed = discord.Embed(title=f"'{craft[1]}' 검수 결과", color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    for text in self.texts_kr:
                        text_passed = craft[0][text[1]]
                        if text_passed:
                            embed.add_field(name=text[0], value="🟢 " + craft[2].get(text[2]) + text[3], inline=False)
                        else:
                            embed.add_field(name=text[0], value="❌ " + craft[2].get(text[2]) + text[4], inline=False)
                    if craft[0]['Unknown_unit_pass'] is False:
                        embed.add_field(name='❗ 알 수 없는 자원이 발견되었어요.', value=str(craft[2]['Unknown_unit']), inline=False)
                    embed.set_footer(text="버그 제보 : cart324#7199")
                    await ctx.send(embed=embed)
                if ctx.guild:
                    await ctx.message.delete()
        except Exception:
            embed = discord.Embed(title="ERROR", color=0xeb4258)
            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
            embed.set_thumbnail(url=author_avatar)
            embed.add_field(name='감각이 없으니 이게 어떻게 된 일이요?', value='어... 하필이면 오류가 영 좋지 않은 곳에 발생했어요.', inline=False)
            embed.add_field(name='내가 버그라니!', value='오류는 자동으로 전달되었으니 문제가 해결될 때까지 기다려주세요.', inline=False)
            await ctx.send(embed=embed)
            error_log = traceback.format_exc(limit=None, chain=True)
            cart = self.bot.get_user(344384179552780289)
            await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")

    # [제목, craft[0]키, craft[2]키, 통과시 추가 문구, 비통과시 추가 문구]
    texts_en = [['Game Version', 'Version_pass', 'Version', '', ''],
                ['Parts Count', 'Count_pass', 'Count', '', ''],
                ['Mass', 'Mass_pass', 'Mass', 't', 't'],
                ['Dimensions', 'Size_pass', 'Size', '', ''],
                ['Points', 'Point_pass', 'Point', 'Pt(s)', 'Pt(s)'],
                ['Forbidden Parts', 'Part_pass', 'Part', 'Hooray! Banned parts not found', ''],
                ['Armor Type', 'ArmorType_pass', 'ArmorType', 'OK', ''],
                ['Hull Material', 'HullType_pass', 'HullType', 'OK', ''],
                ['Tweakscale on Improper Parts', 'Tweak_pass', 'Tweak', 'OK', '']]

    @commands.command(name="check")
    async def craft_EN(self, ctx):
        author_avatar = is_basic_avatar(ctx.author.avatar)
        try:
            crafts = []
            ext_error = False
            for file in ctx.message.attachments:
                if str(file).split(".")[-1] == "craft":
                    file = await file.read()
                    file = file.decode("utf-8")
                    crafts.append(self.check(file))  # 파일 검수
                else:
                    ext_error = True
                    embed = discord.Embed(title="ERROR",
                                          description="OOPS, I can't read the file.\nPlease attach only `.craft` file",
                                          color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="Bug report : cart324#7199")
                    await ctx.send(embed=embed)

            if len(crafts) == 0:
                if ext_error:
                    pass
                else:
                    embed = discord.Embed(title="ERROR",
                                          description="OOPS, The file is missing.\n"
                                                      "Please attach your `.craft` file when using this command.",
                                          color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="Bug report : cart324#7199")
                    await ctx.send(embed=embed)
            else:
                for craft in crafts:
                    craft[2] = length_limit(craft[2])
                    passed = is_passed(craft[0])
                    if passed:
                        embed = discord.Embed(title=f"'{craft[1]}' Results", color=0x00ff95)
                    else:
                        embed = discord.Embed(title=f"'{craft[1]}' Results", color=0xeb4258)
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    for text in self.texts_en:
                        text_passed = craft[0][text[1]]
                        if text_passed:
                            embed.add_field(name=text[0], value="🟢 " + craft[2].get(text[2]) + text[3], inline=False)
                        else:
                            embed.add_field(name=text[0], value="❌ " + craft[2].get(text[2]) + text[4], inline=False)
                    if craft[0]['Unknown_unit_pass'] is False:
                        embed.add_field(name='❗ Unknown Unit Detected', value=str(craft[2]['Unknown_unit']), inline=False)
                    embed.set_footer(text="Bug report : cart324#7199")
                    await ctx.send(embed=embed)
                if ctx.guild:
                    await ctx.message.delete()
        except Exception:
            embed = discord.Embed(title="ERROR", color=0xeb4258)
            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
            embed.set_thumbnail(url=author_avatar)
            embed.add_field(name='This has been the worst bug in the history of bugs, maybe ever.',
                            value='​', inline=False)
            embed.add_field(name='Apply cold water to the bugged area.',
                            value="Achthually, you don't need to. The automatic report is on the way.",
                            inline=False)
            await ctx.send(embed=embed)
            error_log = traceback.format_exc(limit=None, chain=True)
            cart = self.bot.get_user(344384179552780289)
            await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")


def setup(bot):
    bot.add_cog(CraftScanner(bot))
