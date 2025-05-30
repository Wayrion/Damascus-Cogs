import asyncio
import os
import re
import discord
from pystreamable import StreamableApi
from redbot.core import commands
from redbot.core.config import Config
from typing import List, Union
import shutil
from .views import ResolutionView
from .downloader import (
    instagram_downloader,
    reddit_downloader,
    youtube_downloader,
    tiktok_downloader,
)

class MediaParser(commands.Cog):
    """The Reddit parser cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=718395193090375700, force_registration=True
        )

        default_guild = {
            "state": True,
            "ignoreusers": False,
            "ignorebots": True,
            "parseyoutube": False,
            "parseinstagram": True,
            "parsetiktok": True,
            "parsereddit": True,
            "channels": [],
        }

        default_global = {
            "streamable_mail": None,
            "streamable_password": None,
            "instagram_mail": None,
            "instagram_password": None,
            "ytdlp_oauth": None,  # For future use
            "ytdlp_cookies": None,  # For future use
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def remove_output_dir(self, output_dir: str):
        try:
            shutil.rmtree(output_dir)
        except FileNotFoundError:
            pass

    async def cog_load(self):
        current_file_path = os.path.realpath(__file__)
        current_dir = os.path.dirname(current_file_path)

        output_dir = os.path.join(current_dir, "temp")

        try:
            asyncio.create_task(self.remove_output_dir(output_dir))
        except OSError:
            pass

        return await super().cog_load()

    async def upload_media(self, media: str, title: str):
        # media is the str path to the video

        mail: Union[str, None] = await self.config.streamable_mail()
        password: Union[str, None] = await self.config.streamable_password()

        api = StreamableApi(mail, password)

        if not (mail and password):
            prefixes: List[str] = await self.bot.get_valid_prefixes()
            for item in prefixes:
                if item == ("" or None):
                    prefixes.remove(item)

            if len(prefixes) == 0:
                prefixes.append("[p]")

            prefix = prefixes[0]

            url = f"Streamable Mail or Password not set, please set the right credentials in your dms with the bot using\n`{prefix}setmediaparser streamable_mail <mail>` and\n{prefix}setmediaparser streamable_password <password>`"
            return url

        try:
            vid = await asyncio.to_thread(api.upload_video, media, title)
            vid = dict(vid)
            await asyncio.sleep(60)
            url = "https://streamable.com/" + vid["shortcode"]
            return url

        except OSError:
            return

    async def link_parser(self, content: str) -> List[str]:
        # Regular expression to match URLs
        url_pattern = re.compile(r"https?://\S+|www\.\S+")
        urls = url_pattern.findall(content)
        return urls

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        guild = message.guild

        if guild is None:
            return

        if message.author == self.bot.user:
            return

        state = await self.config.guild(guild).state()

        if not state:
            return

        channels = await self.config.guild(guild).channels()

        if message.channel.id not in channels:
            return

        guild = message.guild

        links = await self.link_parser(message.content)
        mail: Union[str, None] = await self.config.instagram_mail()
        password: Union[str, None] = await self.config.instagram_password()
        parseyoutube: bool = await self.config.guild(guild).parseyoutube()
        parsereddit: bool = await self.config.guild(guild).parsereddit()
        parsetiktok: bool = await self.config.guild(guild).parsetiktok()
        parseinstagram: bool = await self.config.guild(guild).parseinstagram()
        ctx: commands.Context = await self.bot.get_context(message)

        for link in links:
            path = None
            async with ctx.typing():
                if ("instagram.com" in link) and parseinstagram:
                    path = await instagram_downloader(link, mail, password)

                elif ("tiktok.com" in link) and parsetiktok:
                    path = await tiktok_downloader(link)

                elif ("reddit.com" in link) and parsereddit:
                    path = await reddit_downloader(link)

                elif ("youtu.be" or "youtube.com" in link) and parseyoutube:
                    path = await youtube_downloader(link)

                else:
                    return

            embed = discord.Embed(
                title="Select Resolution",
                description="Choose the resolution for the download:",
            )

            embed_menu = None
            view = ResolutionView(
                message, path, self, embed_menu
            )  # Self is an instance of Mediaparser
            embed_menu = await message.channel.send(embed=embed, view=view)
            view.embed_menu = embed_menu

    async def send_video(
        self,
        message: discord.Message,
        decision: bool,
        folder_path: str,
        selected_file: str,
    ):
        ctx: commands.Context = await self.bot.get_context(message)
        if not decision:
            self.remove_output_dir(folder_path)
            return
        
        if decision:
            file_path = os.path.join(folder_path, selected_file)
            file_size = os.path.getsize(file_path)
            if message.guild.filesize_limit > file_size:
                await message.channel.send(
                    content=f"Post downloaded by {message.author.mention}",
                    file=discord.File(file_path),
                )
                await asyncio.sleep(10)
                self.remove_output_dir(folder_path)

            else:
                async with ctx.typing():
                    shortcode = await self.upload_media(
                        file_path, str(selected_file)
                    )
                    await message.channel.send(
                        f"Post downloaded by {message.author.mention}\n{shortcode}"
                    )
                    await asyncio.sleep(10)
                self.remove_output_dir(folder_path)

            try:
                await message.delete()
            except discord.Forbidden:
                pass  # No perms to delete

    # SETTINGS
    @commands.is_owner()
    @commands.group()
    async def setmediaparser(self, ctx: commands.Context):
        """
        This settings for the redditparser cog
        """
        pass

    @commands.is_owner()
    @setmediaparser.command()
    async def state(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables the redditparser cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def parse_youtube(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables the parsing youtube links
        """
        await self.config.guild(ctx.guild).parseyoutube.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def parse_tiktok(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables the parsing youtube links
        """
        await self.config.guild(ctx.guild).parsetiktok.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def parse_reddit(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables the parsing youtube links
        """
        await self.config.guild(ctx.guild).parsereddit.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def parse_instagram(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables the parsing youtube links
        """
        await self.config.guild(ctx.guild).parseinstagram.set(state)
        await ctx.send("State set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def ignoreusers(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables link parsing for users
        """
        await self.config.guild(ctx.guild).ignoreusers.set(state)
        await ctx.send("Ignoreusers set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def ignorebots(self, ctx: commands.Context, state: bool):
        """
        This command enables or disables link parsing for bots
        """
        await self.config.guild(ctx.guild).ignorebots.set(state)
        await ctx.send("Ignorebots set to {}".format(state))

    @commands.is_owner()
    @setmediaparser.command()
    async def addchannel(self, ctx: commands.Context, channelID: int):
        """
        This command adds a channel to the list of channels to parse
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.channels() as channels:
            if channelID in channels:
                await ctx.send("Channel already in list")
            else:
                channels.append(channelID)
                await ctx.send(f"Media links will now be parsed in <#{channelID}>")

    @commands.is_owner()
    @setmediaparser.command()
    async def removechannel(self, ctx: commands.Context, channelID: int):
        """
        This command adds a channel to the list of channels to parse
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.channels() as channels:
            if channelID not in channels:
                await ctx.send("Channel not in list")
            else:
                channels.remove(channelID)
                await ctx.send(
                    f"Media links will no longer be parsed in <#{channelID}>"
                )

    @commands.is_owner()
    @commands.dm_only()
    @setmediaparser.command()
    async def streamable_mail(self, ctx: commands.Context, *, ID: str):
        """
        Add your Streamable Mail
        """
        await self.config.streamable_mail.set(ID)
        await ctx.send("Streamable Mail set")

    @commands.is_owner()
    @commands.dm_only()
    @setmediaparser.command()
    async def streamable_password(self, ctx: commands.Context, *, secret: str):
        """
        Add your Streamable Password
        """
        await self.config.streamable_password.set(secret)
        await ctx.send("Streamable Password set")

    @commands.is_owner()
    @commands.dm_only()
    @setmediaparser.command()
    async def instagram_mail(self, ctx: commands.Context, *, ID: str):
        """
        Add your Instagram Mail
        """
        await self.config.instagram_mail.set(ID)
        await ctx.send("Instagram Mail set")

    @commands.is_owner()
    @commands.dm_only()
    @setmediaparser.command()
    async def instagram_password(self, ctx: commands.Context, *, secret: str):
        """
        Add your Instagram Password
        """
        await self.config.instagram_password.set(secret)
        await ctx.send("Instagram Password set")

    @commands.is_owner()
    @setmediaparser.command()
    async def nukeconfig(self, ctx: commands.Context):
        """
        This command nukes the config
        """
        await self.config.clear_all()
        await ctx.send("Config cleared")
