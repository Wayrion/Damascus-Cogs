import discord
from tabulate import tabulate

from redbot.core import Config
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify

from .utils import *

import discord
from PIL import Image, ImageDraw, ImageFont
from redbot.core import Config, commands
import json
import os


class Spellbook(commands.Cog):
    """A D&D 5e Cog for Wizards to manage their spellbooks"""

    def __init__(self, bot):
        self.bot = bot
        default_member = {"Characterpic": None, "Spell": []}
        default_guild = {"db": []}
        self.config = Config.get_conf(self, identifier=42)
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    @commands.command(name="signup")
    @commands.guild_only()
    async def _reg(self, ctx):
        """Sign up to get your own spellbook!"""

        server = ctx.guild
        user = ctx.author
        db = await self.config.guild(server).db()
        if user.id not in db:
            db.append(user.id)
            await self.config.guild(server).db.set(db)
            await self.sendDiscordMessage(
                ctx,
                ":mage: Congrats! :mage:",
                "You have created your spellbook for **{}**, {}.".format(
                    server.name, user.mention
                ),
            )
        else:
            await self.sendDiscordMessage(
                ctx,
                ":warning: Error :warning:",
                "Opps, it seems like you already have a spellbook, {}.".format(
                    user.mention
                ),
            )

    ########################################################

    def load_spell_data(self):
        with open(bundled_data_path(self) / "spells_wizards.json", "r", encoding="utf-8") as f:
            spell_data = json.load(f)
        return spell_data
    
    def create_spell_card(self, spell):
        """Create a spell card image for the given spell data"""

        # Load the spell card template image
        with open(bundled_data_path(self) / "spell_card.png", "rb") as f:
            template = Image.open(f)

        # Load the spell icon image
        icon_path = bundled_data_path(self) / f"{spell.get('icon', 'default')}.png"
        icon = Image.open(icon_path)

        # Resize the spell icon image and paste it onto the template image
        icon = icon.resize((64, 64))
        template.paste(icon, (16, 16), icon)

        # Add the spell name and description to the template image
        draw = ImageDraw.Draw(template)
        name_font = ImageFont.truetype("Roboto-Regular.ttf", size=24)
        desc_font = ImageFont.truetype("Roboto-Regular.ttf", size=16)
        name_width, _ = draw.textsize(spell["name"], font=name_font)
        draw.text((96, 16), spell["name"], font=name_font, fill=(255, 255, 255))
        draw.text((96, 16 + name_width + 8), spell["description"], font=desc_font, fill=(255, 255, 255), align="left", spacing=4)

        # Return the spell card image object
        return template
    

    ########################################################

    @commands.command(name="account")
    async def _account(self, ctx:commands.Context, *spell_names: str):
        """Create a spell card for each spell and attach them to the message"""

        if not spell_names:
            await ctx.send("Please provide at least one spell name.")
            return

        spell_data = self.load_spell_data()
        spell_cards = ["Abi-Dalzim's Horrid Wilting"]

        for name in spell_names:
            spell = next((s for s in spell_data if s["name"].lower() == name.lower()), None)
            if spell:
                spell_card = self.create_spell_card(spell)
                spell_cards.append(spell_card)

        if not spell_cards:
            await ctx.send("No valid spell names provided.")
            return

        for i, spell_card in enumerate(spell_cards):
            filename = f"{i+1}.png"
            spell_card.save(filename)
            with open(filename, "rb") as f:
                file = discord.File(f, filename=filename)
                await ctx.send(file=file)

        for filename in os.listdir():
            if filename.endswith(".png"):
                os.remove(filename)

    @commands.command(name="listwizards")
    @commands.guild_only()
    async def _list_wizards(self, ctx, *, spell_name):
        """List all the Wizards who know a particular spell"""

        wizards = await self.config.all_members(ctx.guild)
        filtered_wizards = [
            {"id": member.id, "username": member.display_name, "user_id": member.id}
            for member in wizards
            if spell_name in member["Spell"]
        ]
        sorted_wizards = sorted(filtered_wizards, key=lambda w: w["username"])
        pages = []

        for i, wizard_chunk in enumerate(pagify(sorted_wizards, page_length=10), start=1):
            table_data = []
            for wizard in wizard_chunk:
                table_data.append([wizard["id"], wizard["username"], wizard["user_id"]])

            table = tabulate(
                table_data,
                headers=["#", "Username", "ID"],
                tablefmt="fancy_grid",
                showindex="always",
                colalign=("center", "center", "center"),
            )
            embed = discord.Embed(colour=discord.Color.red())
            embed.add_field(
                name=f"Filter: {spell_name}",
                value=f"Number of results: {len(filtered_wizards)}",
                inline=False,
            )
            embed.add_field(
                name="Here is a list of all the Wizards who know that spell",
                value=f"```{table}```",
                inline=False,
            )
            embed.set_footer(text=f"Page {i}/{len(sorted_wizards)}")
            pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS)

    @commands.command(name="spellbook")
    @commands.guild_only()
    async def _acc(self, ctx, user: discord.Member = None):
        """Take a peek at your, or someone else's, spellbook."""

        server = ctx.guild
        prefix = ctx.prefix
        db = await self.config.guild(server).db()
        user = user if user else ctx.author
        userdata = await self.config.member(user).all()
        pic = userdata["Characterpic"]

        Pages = []
        Pageno = 1

        if user.id not in db:
            await self.sendDiscordMessage(
                ctx,
                ":warning: Error :warning:",
                "Sadly, you can't peek into other people's Spellbooks without having a spellbook first. \n\nYou can create your spellbook by saying `{}signup` and you'll be all set.".format(
                    prefix
                ),
            )

        for k, v in userdata.items():
            data = discord.Embed(colour=user.colour)
            # data.set_author(name="{}'s Account".format(user.name), icon_url=user.avatar.url)
            if v and not k == "Characterpic":
                if user.avatar.url and not pic:
                    if k == "Spell":
                        for page in list(
                            pagify(str(v), delims=[","], page_length=600, shorten_by=50)
                        ):
                            data.set_author(
                                name=f"{str(user)}'s Spellbook", url=user.avatar.url
                            )
                            data.set_thumbnail(url=user.avatar.url)
                            page = listformatter(page)
                            data.add_field(
                                name="Spells Known:", value=page, inline=False
                            )
                            data.set_footer(
                                text=f"Page {Pageno} out of {len(userdata.items())}"
                            )
                            Pages.append(data)
                    else:
                        data.set_author(
                            name=f"{str(user)}'s Spellbook", url=user.avatar.url
                        )
                        data.set_thumbnail(url=user.avatar.url)
                        data.add_field(name=k, value=v)
                        data.set_footer(
                            text=f"Page {Pageno} out of {len(userdata.items())}"
                        )
                        Pageno += 1
                        Pages.append(data)
                elif pic:
                    if k == "Spell":
                        for page in list(
                            pagify(str(v), delims=[","], page_length=600, shorten_by=50)
                        ):
                            data.set_author(
                                name=f"{str(user)}'s Spellbook", url=user.avatar.url
                            )
                            data.set_thumbnail(url=user.avatar.url)
                            page = listformatter(page)
                            data.add_field(
                                name="Spells Known:", value=page, inline=False
                            )
                            data.set_footer(
                                text=f"Page {Pageno} out of {len(userdata.items())}"
                            )
                            Pages.append(data)
                    else:
                        data.set_author(
                            name=f"{str(user)}'s Spellbook", url=user.avatar.url
                        )
                        data.set_thumbnail(url=user.avatar.url)
                        data.add_field(name=k, value=v)
                        data.set_footer(
                            text=f"Page {Pageno} out of {len(userdata.items())}"
                        )
                        Pageno += 1
                        Pages.append(data)

        if len(Pages) != 0:
            await menu(ctx, Pages, DEFAULT_CONTROLS)
        else:
            await self.sendDiscordMessage(
                ctx,
                ":smiling_face_with_tear: Sad Wizard is sad :smiling_face_with_tear:",
                "{}'s Spellbook is empty.".format(user.mention),
            )

    @commands.group(name="add")
    @commands.guild_only()
    async def add(self, ctx):
        """Update your Spellbook"""
        pass

    @add.command(name="spells")
    @commands.guild_only()
    async def addSpell(self, ctx, *, spell):
        """Which spell(s) do you want to add?"""

        # making a set so that duplicate spells in the same call are not considered
        new_spell_list = processStringToList(spell)
        new_spell_list_valid = []
        new_spell_list_invalid = []
        new_spell_list_duplicate = []
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        guild_group = self.config.member(user)
        db = await self.config.guild(server).db()
        userdata = await self.config.member(user).all()

        if user.id not in db:
            await self.sendDiscordMessage(
                ctx,
                ":warning: Error :warning:",
                "Sadly, you can't add spells without having a spellbook first. \n\nYou can create your spellbook by saying `{}signup` and you'll be all set.".format(
                    prefix
                ),
            )
        else:
            for new_spell in new_spell_list:
                # checks if it's a valid spell
                if not isSpellValid(new_spell):
                    new_spell_list_invalid.append(new_spell)
                    continue
                else:
                    # checks if the user already has this spell
                    if new_spell in userdata["Spell"]:
                        new_spell_list_duplicate.append(new_spell)
                        continue
                    else:
                        new_spell_list_valid.append(new_spell)
                        continue

            # save the valid spells, if any
            if len(new_spell_list_valid) > 0:
                async with guild_group.Spell() as SpellGroup:
                    SpellGroup.extend(new_spell_list_valid)
                    SpellGroup.sort()
                    await self.sendDiscordMessage(
                        ctx,
                        ":sparkles: Success! :sparkles:",
                        "You have copied the following {} into your Spellbook:\n{}".format(
                            "spells" if (len(new_spell_list_valid) > 1) else "spell",
                            ", ".join(new_spell_list_valid),
                        ),
                    )

            # send the duplicate spells, if any
            if len(new_spell_list_duplicate) > 0:
                await self.sendDiscordMessage(
                    ctx,
                    ":coin: I'm saving you money! :coin:",
                    "You already had {} in your Spellbook: \n{}".format(
                        "these spells"
                        if (len(new_spell_list_duplicate) > 1)
                        else "this spell",
                        ", ".join(new_spell_list_duplicate),
                    ),
                )

            # send the invalid spells, if any
            if len(new_spell_list_invalid) > 0:
                await self.sendDiscordMessage(
                    ctx,
                    ":warning: Oh no! :warning:",
                    "The following {} not valid:\n{}\nPlease make sure you spelled it right\nUsed ' and -'s correctly.\nPlease make sure your spell is in [this list](https://pastebin.com/YS7NmYqh)".format(
                        "spells are"
                        if (len(new_spell_list_invalid) > 1)
                        else "spell is",
                        ", ".join(new_spell_list_invalid),
                    ),
                )

    @commands.group(name="remove")
    @commands.guild_only()
    async def remove(self, ctx):
        """Rips pages from your Spellbook"""
        pass

    @remove.command(name="spells")
    @commands.guild_only()
    async def removeSpells(self, ctx, *, spell):
        """Rip pages from your spellbook, as hard as it is to do it"""

        # making a set so that duplicate spells in the same call are not considered
        new_spell_list = processStringToList(spell)
        new_spell_list_valid = []
        new_spell_list_invalid = []
        new_spell_list_unlearned = []
        server = ctx.guild
        user = ctx.author
        prefix = ctx.prefix
        db = await self.config.guild(server).db()
        guild_group = self.config.member(user)
        userdata = await self.config.member(user).all()

        if user.id not in db:
            await self.sendDiscordMessage(
                ctx,
                ":warning: Error :warning:",
                "Sadly, you can't add spells without having a spellbook first. \n\nYou can create your spellbook by saying `{}signup` and you'll be all set.".format(
                    prefix
                ),
            )
        else:
            for new_spell in new_spell_list:
                # checks if it's a valid spell
                if not isSpellValid(new_spell):
                    new_spell_list_invalid.append(new_spell)
                    continue
                else:
                    # checks if the user already has this spell
                    if new_spell in userdata["Spell"]:
                        new_spell_list_valid.append(new_spell)
                        continue
                    else:
                        new_spell_list_unlearned.append(new_spell)
                        continue

                        # send the valid spells, if any
            if len(new_spell_list_valid) > 0:
                async with guild_group.Spell() as SpellGroup:
                    for spell in new_spell_list_valid:
                        try:
                            SpellGroup.remove(spell)
                        except ValueError:
                            new_spell_list_valid.remove(spell)
                            pass
                    SpellGroup.sort()
                    await self.sendDiscordMessage(
                        ctx,
                        ":sob: Success :sob:",
                        "You have ripped the pages of the following {} from your Spellbook:\n{}".format(
                            "spells" if (len(new_spell_list_valid) > 1) else "spell",
                            ", ".join(new_spell_list_valid),
                        ),
                    )

            # send the duplicate spells, if any
            if len(new_spell_list_unlearned) > 0:
                await self.sendDiscordMessage(
                    ctx,
                    ":question: Hmm? :question:",
                    "You don't have {} in your Spellbook:\n{}".format(
                        "these spells"
                        if (len(new_spell_list_unlearned) > 1)
                        else "this spell",
                        ", ".join(new_spell_list_unlearned),
                    ),
                )

                # send the invalid spells, if any
            if len(new_spell_list_invalid) > 0:
                await self.sendDiscordMessage(
                    ctx,
                    ":warning: Oh no! :warning:",
                    "The following {} not valid:\n{}\nPlease make sure you spelled it right\nUsed ' and -'s correctly.\nPlease make sure your spell is in [this list](https://pastebin.com/YS7NmYqh)".format(
                        "spells are" if (len(new_spell_list_invalid)) else "spell is",
                        " ".join(new_spell_list_invalid),
                    ),
                )

    @commands.command()
    @commands.guild_only()
    async def filter(self, ctx, *, filter):
        """Searches for Wizards with knowledge of a particular spell"""

        filter = processStringToList(filter).pop()
        server = ctx.guild
        db = await self.config.guild(server).db()
        FilteredList = []
        Pages = []
        Resultsperpage = 5
        PageNo = 1

        if len(db) == 0:
            await ctx.send("There are no spellbooks in this library")

        if not isSpellValid(filter):
            await self.sendDiscordMessage(
                ctx,
                ":warning: Oh no! :warning:",
                "{} is not a valid spell. Please make sure you spelled it right\nUsed ' and -'s correctly.\nPlease make sure your spell is in [this list](https://pastebin.com/YS7NmYqh)".format(
                    filter
                ),
            )
        else:
            for id in db:
                user = server.get_member(id)
                if user is None:
                    continue # TODO: drop stale users
                nickname = user.display_name
                nickname = nickname[0:20]
                userdata = await self.config.member(user).all()

                if filter in userdata["Spell"]:
                    FilteredList.extend([[f"{nickname}", f"{user.id}"]])

            if len(FilteredList) == 0:
                await self.sendDiscordMessage(
                    ctx,
                    ":warning: Oh no! :warning:",
                    "There are no Wizards who know {}".format(filter),
                )
            else:
                SplitList = [
                    FilteredList[i * Resultsperpage : (i + 1) * Resultsperpage]
                    for i in range(
                        (len(FilteredList) + Resultsperpage - 1) // Resultsperpage
                    )
                ]
                for Split in SplitList:
                    tabulatedlist = f"""```{tabulate(Split, headers=["#", "Username","ID"], tablefmt="fancy_grid", showindex="always", colalign=("center", "center", "center"))}```"""
                    e = discord.Embed(colour=discord.Color.red())
                    e.add_field(
                        name=f"Filter: {filter}",
                        value=f"Number of results: {len(FilteredList)}",
                        inline=False,
                    )
                    e.add_field(
                        name="Here is a list of all the Wizards who know that spell",
                        value=tabulatedlist,
                        inline=False,
                    )
                    e.set_footer(text=f"Page {PageNo}/{len(SplitList)}")
                    PageNo += 1
                    Pages.append(e)

                await menu(ctx, Pages, DEFAULT_CONTROLS)

    async def sendDiscordMessage(self, ctx, title, text):
        data = discord.Embed(colour=ctx.author.colour)
        data.add_field(name=title, value=text)
        await ctx.send(embed=data)
