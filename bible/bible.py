import discord
import os
import json
from redbot.core import commands, Config
from typing import Union
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.data_manager import bundled_data_path

class Bible(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=718395193090375700)
        default_global = {
            "Notes": []
        }
        self.config.register_global(**default_global)

    @commands.group()
    async def bible(self, ctx: commands.Context):
        """Searches for a verse or chapter in the bible"""
        pass

    @bible.command()
    async def lookup(self, ctx: commands.Context, book: str, arg: str):
        """Searches for a verse or chapter in the bible"""
        try:
            book = book.strip()
            book = book.capitalize()
            chapter, verse = arg.split(':')
            chapter = int(chapter)
        except:
            await ctx.send("Invalid argument")
            return
        
        try:
            verse_min , verse_max = verse.split('-')
            verse_min = int(verse_min)
            verse_max = int(verse_max)

        except:
            try:
                verse_min = int(verse)
                verse_max = int(verse)
            except ValueError:
                await ctx.send("Invalid argument")
                return

        path = bundled_data_path(self) / "bible"

        try:
            with open(os.path.join(path, book + '.json')) as json_file:
                data = json.load(json_file)
                embeds = []
                book_name = data["book"]
                chapters = data["chapters"]
                chapter = chapters[chapter-1]
                description = ""

                try:
                    chapter.get("verses")[verse_min-1:verse_max]
                except IndexError:
                    await ctx.send("Verse not found")
                    return

                for verse in chapter.get("verses")[verse_min-1:verse_max]:
                    description += f"[{verse['verse']}]" + verse['text'] + "\n"
                    async with self.config.Notes() as notes:
                        for note in notes:
                            if note["book"] == book_name:
                                if str(note["chapter"]) == str(chapter["chapter"]):# Compare with chapter index
                                    if str(note["verse"]) == str(verse["verse"]):
                                        description += str(box(text="- " + note["note"], lang="diff") + "\n\n")

                for descript in pagify(description, page_length=3950, delims=["```", "\n\n", "\n", "**"]):
                    embed = discord.Embed(title=book_name, description=descript, color=discord.Color.green())
                    embeds.append(embed)

                await menu(ctx, embeds, controls=DEFAULT_CONTROLS, timeout=30)

        except FileNotFoundError:
            await ctx.send("Book not found")

    @commands.group()
    async def memory(self, ctx: commands.Context):
        """Manage for each verse or chapter of the bible"""
        pass

    @memory.command()
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def add(self, ctx: commands.Context, book: str, arg: str , *, note: str):
        """Adds a note to a verse or chapter"""

        book = book.strip()
        book = book.capitalize()
        chapter, verse = arg.split(':')
        chapter = int(chapter)

        try:
            verse = int(verse)

        except ValueError:
            await ctx.send("Verse not found")

        async with self.config.Notes() as notes:
            notes_copy = notes 
            for i, note_data in enumerate(notes_copy, start=1):
                note_data["number"] = i
                #notes.append(note)
            notes.append({"number": len(notes)+1, "book": book, "chapter": chapter, "verse": verse, "note": note})
        await ctx.send("Note added")

    @memory.command()
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def remove(self, ctx: commands.Context, number: int):
        """Removes a note to a verse or chapter"""
    
        async with self.config.Notes() as notes:
            notes_copy = notes

            try:
                notes_copy[number-1]
            except IndexError:
                await ctx.send("Note not found")
                return

            for note in notes:
                if note["number"] == number:
                    notes.remove(note)
                    await ctx.send("Note removed")

            for i, note_data in enumerate(notes_copy, start=1):
                note_data["number"] = i

    @memory.command()
    async def list(self, ctx: commands.Context, book: Union[str, None] = None, arg: Union[str, None] = None):
        """Lists all notes or notes for a verse or chapter"""

        description = ""
        embeds= []

        if book is not None:
            book = book.strip()
            book = book.capitalize()
        
        if arg is not None:
            chapter, verse = arg.split(':')
            chapter = int(chapter) if chapter else None
            verse = int(verse) if verse else None
        else:
            chapter = None
            verse = None

        if book is None and arg is None:
            async with self.config.Notes() as notes:
                for note in notes:
                    description += f"**{note['number']}. {note['book']} {note['chapter']}:{note['verse']}**\n```diff\n- {note['note']}\n```\n\n"

        elif book is not None and arg is None:
            async with self.config.Notes() as notes:
                for note in notes:
                    if note["book"] == book:
                        description += f"**{note['number']}. {note['book']} {note['chapter']}:{note['verse']}**\n```diff\n- {note['note']}\n```\n\n"
        
        elif book is not None and arg is not None:
            if chapter is not None and verse is None:
                async with self.config.Notes() as notes:
                    for note in notes:
                        if note["book"] == book and note["chapter"] == chapter:
                            description += f"**{note['number']}. {note['book']} {note['chapter']}:{note['verse']}**\n```diff\n- {note['note']}\n```\n"
            elif chapter is not None and verse is not None:
                async with self.config.Notes() as notes:
                    for note in notes:
                        if note["book"] == book and note["chapter"] == chapter and note["verse"] == verse:
                            description += f"**{note['number']}. {note['book']} {note['chapter']}:{note['verse']}**\n```diff\n- {note['note']}\n```\n"

        if description == "":
            await ctx.send("No notes found")
        else:
            PageNumber = 1
            for descript in pagify(description, page_length=3900, delims=["\n\n"]):
                embed = discord.Embed(title="Notes", description=descript, color=discord.Color.green())
                embed.set_footer(text="Page: {} / {}".format(PageNumber, len(list(pagify(description, page_length=3900, delims=["\n\n"])))))
                embeds.append(embed)
                PageNumber += 1

            await menu(ctx, embeds, controls=DEFAULT_CONTROLS, timeout=30)

    @bible.command()
    async def search(self, ctx: commands.Context, *, arg: str):
        """Searches for a verse or chapter"""

        folder_path = bundled_data_path(self) / "bible"
        description = ""
        embeds = []

        for filename in os.listdir(folder_path):
            with open(os.path.join(folder_path, filename), "r") as file:
                data = json.load(file)
                book_name = data["book"]
                chapters = data["chapters"]
                for chapter in chapters:
                    chapter_num = chapter["chapter"]
                    verses = chapter["verses"]
                    for verse in verses:
                        verse_num = verse["verse"]
                        verse_text = verse["text"]
                        if arg.lower() in verse_text.lower():
                            description += f"**{book_name} {chapter_num}:{verse_num}**\n{verse_text}\n\n"

        if description == "":
            await ctx.send("No matches found")
        else:
            PageNumber = 1
            for descript in pagify(description, page_length=3950, delims=["\n\n"]):
                embed = discord.Embed(title="Search", description=descript, color=discord.Color.green())
                embed.set_footer(text="Page: {} / {}".format(PageNumber, len(list(pagify(description, page_length=3900, delims=["\n\n"])))))
                embeds.append(embed)
                PageNumber += 1

            await menu(ctx, embeds, controls=DEFAULT_CONTROLS, timeout=30)

    @commands.command()
    @commands.is_owner()
    async def removeallnotes(self, ctx: commands.Context):
        """Clears all notes"""
        await self.config.clear_all()
        await ctx.send("All Notes removed")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore CommandNotFound errors

        if isinstance(error, (AttributeError, ValueError)):
            await ctx.send("Incorrect parameters, please try again. Use `{}help` for more information.".format(ctx.prefix))
        else:
            # Re-raise the error if it's not an AttributeError or ValueError
            raise error