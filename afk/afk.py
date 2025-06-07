import datetime
from discord.message import Message
from discord.user import User
from discord.activity import ActivityTypes
from discord.embeds import Embed

from discord.member import Member
from discord.guild import Guild

from re import Match, Pattern
from redbot.core.config import Group


import discord
from redbot.core import Config, checks, commands

try:
    from slashtags import menu
except ModuleNotFoundError:
    from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

import re
from typing import Any, Literal

IMAGE_LINKS: Pattern[str] = re.compile(r"(http[s]?:\/\/[^\"\']*\.(?:png|jpg|jpeg|gif|png))")


class Afk(commands.Cog):
    """Le Afk cog
    Originally called Away but changed to avoid conflicts with the Away cog
    Check out the original [here](https://github.com/aikaterna/aikaterna-cogs)"""

    default_global_settings: dict[str, list[Any]] = {"ign_servers": []}
    default_guild_settings: dict[str, bool | list[Any]] = {"TEXT_ONLY": False, "BLACKLISTED_MEMBERS": []}
    default_user_settings: dict[str, bool | int | dict[Any, Any] | list[Any]] = {
        "MESSAGE": False,
        "IDLE_MESSAGE": False,
        "DND_MESSAGE": False,
        "OFFLINE_MESSAGE": False,
        "GAME_MESSAGE": {},
        "STREAMING_MESSAGE": False,
        "LISTENING_MESSAGE": False,
        "PINGS": [],
        "TIME": 0,
    }

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=718395193090375700, force_registration=True
        )  # Changed Identifier
        self.config.register_global(**self.default_global_settings)
        self.config.register_guild(**self.default_guild_settings)
        self.config.register_user(**self.default_user_settings)

    def _draw_play(self, song) -> str:
        song_start_time = song.start
        total_time = song.duration
        current_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)
        elapsed_time = current_time - song_start_time
        sections = 12
        loc_time: int = round(number=(elapsed_time / total_time) * sections, ndigits=None)  # 10 sections

        bar_char = "\N{BOX DRAWINGS HEAVY HORIZONTAL}"
        seek_char = "\N{RADIO BUTTON}"
        play_char = "\N{BLACK RIGHT-POINTING TRIANGLE}"
        msg = "\n" + play_char + " "

        for i in range(sections):
            if i == loc_time:
                msg += seek_char
            else:
                msg += bar_char

        msg += " `{:.7}`/`{:.7}`".format(str(elapsed_time), str(total_time))
        return msg

    async def add_ping(self, message: discord.Message, author: discord.User | discord.Member) -> None:
        """
        Adds a user to the list of pings
        """
        user_config: Group = self.config.user(user=author)
        async with user_config.PINGS() as pingslist:
            pingslist.append(
                {
                    "whopinged": message.author.mention,
                    "msgurl": message.jump_url,
                    "channel": message.channel.mention,
                    "timestamp": f"<t:{round(number=datetime.datetime.now().timestamp())}:R>",
                    "messagecontent": message.content[0:500],
                    "pageno": len(pingslist) + 1,
                }
            )

    async def remove_ping(self, author: discord.User | discord.Member) -> None:
        """
        Adds a user to the list of pings
        """
        user_config: Group = self.config.user(user=author)
        await user_config.PINGS.clear()

    async def pingmenu(self, ctx: commands.Context, author: discord.User | discord.Member) -> None:
        """
        Returns a menu of the people who pinged you
        """
        user_config: Group = self.config.user(user=author)
        menulist: list[Any] = []
        async with user_config.PINGS() as pingslist:
            for ping in pingslist:
                embed: discord.Embed = discord.Embed(
                    title="Ping Menu",
                    description="Here's a menu with the list of people who pinged you while you were AFK",
                    color=discord.Color.random(),
                )
                _ = embed.add_field(
                    name="Who pinged?:", value=ping["whopinged"], inline=False
                )
                _ = embed.add_field(
                    name="Message URL:",
                    value=f"[Click Here]({ping['msgurl']})",
                    inline=False,
                )
                _ = embed.add_field(name="Channel:", value=ping["channel"], inline=False)
                _ = embed.add_field(name="When?:", value=ping["timestamp"], inline=False)
                _ = embed.set_footer(text=f"Page no: {(ping['pageno'])}/{len(pingslist)}")
                menulist.append(embed)

        await menu(ctx, pages=menulist, controls=DEFAULT_CONTROLS, timeout=15)

    async def make_embed_message(self, author: discord.User | discord.Member, message: discord.Message, state=None) -> discord.Embed:
        """
        Makes the embed reply
        """
        avatar: discord.Asset = author.display_avatar  # This will return default avatar if no avatar is present
        color: int = author.color

        if message:
            link: Any = IMAGE_LINKS.search(message)
            if link:
                message: Any | discord.Message = message.replace(link.group(0), " ")
            message: Any | discord.Message = message + f" (<t:{await self.config.user(user=author).TIME()}:R>)"

        if state == "away":
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently away", icon_url=avatar
            )
        elif state == "idle":
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently idle", icon_url=avatar
            )
        elif state == "dnd":
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently do not disturb",
                icon_url=avatar,
            )
        elif state == "offline":
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently offline", icon_url=avatar
            )
        elif state == "gaming":
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently playing {author.activity.name}",
                icon_url=avatar,
            )
            em.title = getattr(author.activity, "details", None)
            thumbnail: Any | None = getattr(author.activity, "large_image_url", None)
            if thumbnail:
                _ = em.set_thumbnail(url=thumbnail)
        elif state == "gamingcustom":
            status: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.playing
            ]
            em: discord.Embed = discord.Embed(description=message, color=color)
            _ = em.set_author(
                name=f"{author.display_name} is currently playing {status[0].name}",
                icon_url=avatar,
            )
            em.title = getattr(status[0], "details", None)
            thumbnail: Any | None = getattr(status[0], "large_image_url", None)
            if thumbnail:
                _ = em.set_thumbnail(url=thumbnail)
        elif state == "listening":
            em: discord.Embed = discord.Embed(color=author.activity.color)
            url: str = f"https://open.spotify.com/track/{author.activity.track_id}"
            artist_title: str = f"{author.activity.title} by " + ", ".join(
                a for a in author.activity.artists
            )
            
            _ = em.set_author(
                name=f"{author.display_name} is currently listening to",
                icon_url=avatar,
                url=url,
            )
            em.description = (
                f"{message}\n "
                f"[{artist_title}]({url})\n"
                f"{self._draw_play(song=author.activity)}"
            )

            _ = em.set_thumbnail(url=author.activity.album_cover_url)
        elif state == "listeningcustom":
            activity: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.listening
            ]
            em: discord.Embed = discord.Embed(color=activity[0].color)
            url: str = f"https://open.spotify.com/track/{activity[0].track_id}"
            artist_title: str = f"{activity[0].title} by " + ", ".join(
                a for a in activity[0].artists
            )
            _ = em.set_author(
                name=f"{author.display_name} is currently listening to",
                icon_url=avatar,
                url=url,
            )
            em.description = (
                f"{message}\n "
                f"[{artist_title}]({url})\n"
                f"{self._draw_play(song=activity[0])}"
            )
            _ = em.set_thumbnail(url=activity[0].album_cover_url)
        elif state == "streaming":
            color: int = int("6441A4", 16)
            em: discord.Embed = discord.Embed(color=color)
            em.description = message + "\n" + author.activity.url
            em.title = getattr(author.activity, "details", None)
            _ = em.set_author(
                name=f"{author.display_name} is currently streaming {author.activity.name}",
                icon_url=avatar,
            )
        elif state == "streamingcustom":
            activity: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.streaming
            ]
            color = int("6441A4", 16)
            em = discord.Embed(color=color)
            em.description = message + "\n" + activity[0].url
            em.title = getattr(author.activity, "details", None)
            em.set_author(
                name=f"{author.display_name} is currently streaming {activity[0].name}",
                icon_url=avatar,
            )
        else:
            em = discord.Embed(color=color)
            em.set_author(
                name="{} is currently away".format(author.display_name), icon_url=avatar
            )
        if link and state not in ["listening", "listeningcustom", "gaming"]:
            em.set_image(url=link.group(0))
        return em

    async def find_user_mention(self, message: discord.Message):
        """
        Replaces user mentions with their username
        """
        for word in message.split():
            match: Match[str] | None = re.search(r"<@!?([0-9]+)>", word)
            if match:
                user: User = await self.bot.fetch_user(int(match.group(1)))
                message: Any | Message = re.sub(match.re, "@" + user.name, message)
        return message

    async def make_text_message(self, author: discord.User | discord.Member, message: discord.Message, state=None):
        """
        Makes the message to display if embeds aren't available
        """
        message: Message | Any = await self.find_user_mention(message)

        if state == "away":
            msg: str = f"{author.display_name} is currently away"
        elif state == "idle":
            msg: str = f"{author.display_name} is currently idle"
        elif state == "dnd":
            msg: str = f"{author.display_name} is currently do not disturb"
        elif state == "offline":
            msg: str = f"{author.display_name} is currently offline"
        elif state == "gaming":
            msg: str = f"{author.display_name} is currently playing {author.activity.name} "
        elif state == "gamingcustom":
            status: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.playing
            ]
            msg = f"{author.display_name} is currently playing {status[0].name}"
        elif state == "listening":
            artist_title = f"{author.activity.title} by " + ", ".join(
                a for a in author.activity.artists
            )
            currently_playing: str = self._draw_play(song=author.activity)
            msg: str = f"{author.display_name} is currently listening to {artist_title}\n{currently_playing}"
        elif state == "listeningcustom":
            status: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.listening
            ]
            artist_title = f"{status[0].title} by " + ", ".join(
                a for a in status[0].artists
            )
            currently_playing: str = self._draw_play(song=status[0])
            msg: str = f"{author.display_name} is currently listening to {artist_title}\n{currently_playing}"
        elif state == "streaming":
            msg: str = (
                f"{author.display_name} is currently streaming at {author.activity.url}"
            )
        elif state == "streamingcustom":
            status: list[ActivityTypes | Any] = [
                c for c in author.activities if c.type == discord.ActivityType.streaming
            ]
            msg: str = f"{author.display_name} is currently streaming at {status[0].url}"
        else:
            msg: str = f"{author.display_name} is currently away "

        if message != " " and state != "listeningcustom":
            msg += f" and has set the following message: `{message}`"
        elif message != " " and state == "listeningcustom":
            msg += f"\n\nCustom message: `{message}`"

        msg = msg + f" (<t:{await self.config.user(author).TIME()}:R>)"
        return msg

    async def is_mod_or_admin(self, member: discord.Member):
        guild = member.guild
        if member == guild.owner:
            return True
        if await self.bot.is_owner(member):
            return True
        if await self.bot.is_admin(member):
            return True
        if await self.bot.is_mod(member):
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        guild = message.guild

        if not guild or not message.mentions or message.author.bot:
            return
        if not message.channel.permissions_for(guild.me).send_messages:
            return

        blocked_guilds = await self.config.ign_servers()
        guild_config = await self.config.guild(guild).all()

        for author in message.mentions:
            if (
                guild.id in blocked_guilds and not await self.is_mod_or_admin(author)
            ) or author.id in guild_config["BLACKLISTED_MEMBERS"]:
                continue
            user_data = await self.config.user(author).all()
            embed_links = message.channel.permissions_for(guild.me).embed_links

            away_msg = user_data["MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(away_msg, list)
                and away_msg[1] is not None
                and away_msg[1] < 5
            ):
                await self.config.user(author).MESSAGE.set((away_msg[0], 5))
                away_msg = away_msg[0], 5
            if away_msg:
                if type(away_msg) in [tuple, list]:
                    # This is just to keep backwards compatibility
                    away_msg, delete_after = away_msg
                else:
                    delete_after = None
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(author, away_msg, "away")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(author, away_msg, "away")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            idle_msg = user_data["IDLE_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(idle_msg, list)
                and idle_msg[1] is not None
                and idle_msg[1] < 5
            ):
                await self.config.user(author).IDLE_MESSAGE.set((idle_msg[0], 5))
                idle_msg = idle_msg[0], 5
            if idle_msg and author.status == discord.Status.idle:
                if type(idle_msg) in [tuple, list]:
                    idle_msg, delete_after = idle_msg
                else:
                    delete_after = None
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(author, idle_msg, "idle")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(author, idle_msg, "idle")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            dnd_msg = user_data["DND_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if isinstance(dnd_msg, list) and dnd_msg[1] is not None and dnd_msg[1] < 5:
                await self.config.user(author).DND_MESSAGE.set((dnd_msg[0], 5))
                dnd_msg = dnd_msg[0], 5
            if dnd_msg and author.status == discord.Status.dnd:
                if type(dnd_msg) in [tuple, list]:
                    dnd_msg, delete_after = dnd_msg
                else:
                    delete_after = None
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(author, dnd_msg, "dnd")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(author, dnd_msg, "dnd")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            offline_msg = user_data["OFFLINE_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(offline_msg, list)
                and offline_msg[1] is not None
                and offline_msg[1] < 5
            ):
                await self.config.user(author).OFFLINE_MESSAGE.set((offline_msg[0], 5))
                offline_msg = offline_msg[0], 5
            if offline_msg and author.status == discord.Status.offline:
                if type(offline_msg) in [tuple, list]:
                    offline_msg, delete_after = offline_msg
                else:
                    delete_after = None
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(author, offline_msg, "offline")
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(author, offline_msg, "offline")
                    await self.add_ping(message, author)
                    await message.channel.send(msg, delete_after=delete_after)
                continue
            streaming_msg = user_data["STREAMING_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(streaming_msg, list)
                and streaming_msg[1] is not None
                and streaming_msg[1] < 5
            ):
                await self.config.user(author).STREAMING_MESSAGE.set(
                    (streaming_msg[0], 5)
                )
                streaming_msg = streaming_msg[0], 5
            if streaming_msg and type(author.activity) is discord.Streaming:
                streaming_msg, delete_after = streaming_msg
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(
                        author, streaming_msg, "streaming"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(
                        author, streaming_msg, "streaming"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            if streaming_msg and type(author.activity) is discord.CustomActivity:
                stream_status = [
                    c
                    for c in author.activities
                    if c.type == discord.ActivityType.streaming
                ]
                if not stream_status:
                    continue
                streaming_msg, delete_after = streaming_msg
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(
                        author, streaming_msg, "streamingcustom"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(
                        author, streaming_msg, "streamingcustom"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            listening_msg = user_data["LISTENING_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(listening_msg, list)
                and listening_msg[1] is not None
                and listening_msg[1] < 5
            ):
                await self.config.user(author).LISTENING_MESSAGE.set(
                    (listening_msg[0], 5)
                )
                listening_msg = listening_msg[0], 5
            if listening_msg and type(author.activity) is discord.Spotify:
                listening_msg, delete_after = listening_msg
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(
                        author, listening_msg, "listening"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(
                        author, listening_msg, "listening"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            if listening_msg and type(author.activity) is discord.CustomActivity:
                listening_status = [
                    c
                    for c in author.activities
                    if c.type == discord.ActivityType.listening
                ]
                if not listening_status:
                    continue
                listening_msg, delete_after = listening_msg
                if embed_links and not guild_config["TEXT_ONLY"]:
                    em = await self.make_embed_message(
                        author, listening_msg, "listeningcustom"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        embed=em,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                elif (embed_links and guild_config["TEXT_ONLY"]) or not embed_links:
                    msg = await self.make_text_message(
                        author, listening_msg, "listeningcustom"
                    )
                    await self.add_ping(message, author)
                    await message.channel.send(
                        msg,
                        delete_after=delete_after,
                        reference=message,
                        mention_author=False,
                    )
                continue
            gaming_msgs = user_data["GAME_MESSAGE"]
            # Convert possible `delete_after` of < 5s of before PR#212
            if (
                isinstance(gaming_msgs, list)
                and gaming_msgs[1] is not None
                and gaming_msgs[1] < 5
            ):
                await self.config.user(author).GAME_MESSAGE.set((gaming_msgs[0], 5))
                gaming_msgs = gaming_msgs[0], 5
            if gaming_msgs and type(author.activity) in [
                discord.Game,
                discord.Activity,
            ]:
                for game in gaming_msgs:
                    if game in author.activity.name.lower():
                        game_msg, delete_after = gaming_msgs[game]
                        if embed_links and not guild_config["TEXT_ONLY"]:
                            em = await self.make_embed_message(
                                author, game_msg, "gaming"
                            )
                            await self.add_ping(message, author)
                            await message.channel.send(
                                embed=em,
                                delete_after=delete_after,
                                reference=message,
                                mention_author=False,
                            )
                            break  # Let's not accidentally post more than one
                        elif (
                            embed_links and guild_config["TEXT_ONLY"]
                        ) or not embed_links:
                            msg = await self.make_text_message(
                                author, game_msg, "gaming"
                            )
                            await self.add_ping(message, author)
                            await message.channel.send(
                                msg,
                                delete_after=delete_after,
                                reference=message,
                                mention_author=False,
                            )
                            break
            if gaming_msgs and type(author.activity) is discord.CustomActivity:
                game_status = [
                    c
                    for c in author.activities
                    if c.type == discord.ActivityType.playing
                ]
                if not game_status:
                    continue
                for game in gaming_msgs:
                    if game in game_status[0].name.lower():
                        game_msg, delete_after = gaming_msgs[game]
                        if embed_links and not guild_config["TEXT_ONLY"]:
                            em: Embed = await self.make_embed_message(
                                author, message=game_msg, state="gamingcustom"
                            )
                            await self.add_ping(message, author)
                            _ = await message.channel.send(
                                embed=em,
                                delete_after=delete_after,
                                reference=message,
                                mention_author=False,
                            )
                            break  # Let's not accidentally post more than one
                        elif (
                            embed_links and guild_config["TEXT_ONLY"]
                        ) or not embed_links:
                            msg: str = await self.make_text_message(
                                author, message=game_msg, state="gamingcustom"
                            )
                            await self.add_ping(message, author)
                            _ = await message.channel.send(
                                msg,
                                delete_after=delete_after,
                                reference=message,
                                mention_author=False,
                            )
                            break

    @commands.command(name="away", aliases=["afk"])
    async def away_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Tell the bot you're away or back.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        user_config: dict[str, Any] = await self.config.user(user=author).all()
        mess = await self.config.user(user=author).MESSAGE()

        if mess:
            await self.config.user(user=author).MESSAGE.set(value=False)
            await self.config.user(user=author).TIME.set(value=0)
            msg = "You're now back."
            await ctx.send(content=msg)
            if len(user_config["PINGS"]) != 0:
                await self.pingmenu(ctx, author)
                await self.remove_ping(author)
            else:
                pass
        else:
            if message is None:
                await self.config.user(user=author).MESSAGE.set(value=(" ", delete_after))
            else:
                await self.config.user(user=author).MESSAGE.set(value=(message, delete_after))
            await self.config.user(user=author).TIME.set(
                value=round(number=datetime.datetime.now().timestamp())
            )
            msg = "You're now set as away."
            await ctx.send(content=msg)

    @commands.command(name="idle")
    async def idle_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're idle.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        mess = await self.config.user(user=author).IDLE_MESSAGE()
        if mess:
            await self.config.user(user=author).IDLE_MESSAGE.set(value=False)
            msg = "The bot will no longer reply for you when you're idle."
        else:
            if message is None:
                await self.config.user(user=author).IDLE_MESSAGE.set(value=(" ", delete_after))
            else:
                await self.config.user(user=author).IDLE_MESSAGE.set(value=(message, delete_after))
            msg = "The bot will now reply for you when you're idle."
        await ctx.send(content=msg)

    @commands.command(name="offline")
    async def offline_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're offline.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        mess = await self.config.user(author).OFFLINE_MESSAGE()
        if mess:
            await self.config.user(author).OFFLINE_MESSAGE.set(False)
            msg = "The bot will no longer reply for you when you're offline."
        else:
            if message is None:
                await self.config.user(author).OFFLINE_MESSAGE.set((" ", delete_after))
            else:
                await self.config.user(author).OFFLINE_MESSAGE.set(
                    (message, delete_after)
                )
            msg = "The bot will now reply for you when you're offline."
        await ctx.send(msg)

    @commands.command(name="dnd", aliases=["donotdisturb"])
    async def donotdisturb_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're dnd.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        mess = await self.config.user(user=author).DND_MESSAGE()
        if mess:
            await self.config.user(user=author).DND_MESSAGE.set(value=False)
            msg = "The bot will no longer reply for you when you're set to do not disturb."
        else:
            if message is None:
                await self.config.user(user=author).DND_MESSAGE.set(value=(" ", delete_after))
            else:
                await self.config.user(user=author).DND_MESSAGE.set(value=(message, delete_after))
            msg = "The bot will now reply for you when you're set to do not disturb."
        await ctx.send(content=msg)

    @commands.command(name="streaming")
    async def streaming_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're streaming.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        mess = await self.config.user(user=author).STREAMING_MESSAGE()
        if mess:
            await self.config.user(user=author).STREAMING_MESSAGE.set(False)
            msg = "The bot will no longer reply for you when you're mentioned while streaming."
        else:
            if message is None:
                await self.config.user(user=author).STREAMING_MESSAGE.set(
                    value=(" ", delete_after)
                )
            else:
                await self.config.user(author).STREAMING_MESSAGE.set(
                    value=(message, delete_after)
                )
            msg = (
                "The bot will now reply for you when you're mentioned while streaming."
            )
        await ctx.send(content=msg)

    @commands.command(name="listening")
    async def listening_(
        self, ctx: commands.Context, delete_after: int | None = None, *, message: str = " "
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're listening to Spotify.

        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: discord.User = ctx.message.author
        mess = await self.config.user(user=author).LISTENING_MESSAGE()
        if mess:
            await self.config.user(user=author).LISTENING_MESSAGE.set(value=False)
            msg = "The bot will no longer reply for you when you're mentioned while listening to Spotify."
        else:
            await self.config.user(user=author).LISTENING_MESSAGE.set(
                value=(message, delete_after)
            )
            msg = "The bot will now reply for you when you're mentioned while listening to Spotify."
        await ctx.send(content=msg)

    @commands.command(name="gaming")
    async def gaming_(
        self, ctx: commands.Context, game: str, delete_after: int | None = None, *, message: str = None
    ) -> discord.Message | None:
        """
        Set an automatic reply when you're playing a specified game.

        `game` The game you would like automatic responses for
        `delete_after` Optional seconds to delete the automatic reply. Must be minimum 5 seconds
        `message` The custom message to display when you're mentioned

        Use "double quotes" around a game's name if it is more than one word.
        """
        if delete_after is not None and delete_after < 5:
            return await ctx.send(
                content="Please set a time longer than 5 seconds for the `delete_after` argument"
            )

        author: User | Member = ctx.message.author
        mess = await self.config.user(user=author).GAME_MESSAGE()
        if game.lower() in mess:
            del mess[game.lower()]
            await self.config.user(user=author).GAME_MESSAGE.set(value=mess)
            msg: str = f"The bot will no longer reply for you when you're playing {game}."
        else:
            if message is None:
                mess[game.lower()] = (" ", delete_after)
            else:
                mess[game.lower()] = (message, delete_after)
            await self.config.user(user=author).GAME_MESSAGE.set(value=mess)
            msg: str = f"The bot will now reply for you when you're playing {game}."
        await ctx.send(content=msg)

    @commands.command(name="toggleaway")
    @commands.guild_only()
    @checks.admin_or_permissions(administrator=True)
    async def _ignore(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """
        Toggle away messages on the whole server or a specific guild member.

        Mods, Admins and Bot Owner are immune to this.
        """
        guild: Guild | None = ctx.message.guild
        if member:
            bl_mems: list[int] = await self.config.guild(guild).BLACKLISTED_MEMBERS()
            if member.id not in bl_mems:
                bl_mems.append(member.id)
                await self.config.guild(guild).BLACKLISTED_MEMBERS.set(value=bl_mems)
                msg: str = f"Away messages will not appear when {member.display_name} is mentioned in this guild."
                await ctx.send(content=msg)
            elif member.id in bl_mems:
                bl_mems.remove(member.id)
                await self.config.guild(guild).BLACKLISTED_MEMBERS.set(value=bl_mems)
                msg: str = f"Away messages will appear when {member.display_name} is mentioned in this guild."
                await ctx.send(content=msg)
            return
        if guild.id in (await self.config.ign_servers()):
            guilds = await self.config.ign_servers()
            guilds.remove(guild.id)
            await self.config.ign_servers.set(value=guilds)
            message = "Not ignoring this guild anymore."
        else:
            guilds = await self.config.ign_servers()
            guilds.append(guild.id)
            await self.config.ign_servers.set(value=guilds)
            message = "Ignoring this guild."
        await ctx.send(content=message)

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(administrator=True)
    async def awaytextonly(self, ctx: commands.Context) -> None:
        """
        Toggle forcing the guild's away messages to be text only.

        This overrides the embed_links check this cog uses for message sending.
        """
        text_only = await self.config.guild(guild=ctx.guild).TEXT_ONLY()
        if text_only:
            message = "Away messages will now be embedded or text only based on the bot's permissions for embed links."
        else:
            message = "Away messages are now forced to be text only, regardless of the bot's permissions for embed links."
        await self.config.guild(guild=ctx.guild).TEXT_ONLY.set(value=not text_only)
        await ctx.send(content=message)

    @commands.command(name="awaysettings", aliases=["awayset"])
    async def away_settings(self, ctx: commands.Context) -> None:
        """View your current away settings"""
        author: discord.User = ctx.author
        msg = ""
        data: dict[str, str] = {
            "MESSAGE": "Away",
            "IDLE_MESSAGE": "Idle",
            "DND_MESSAGE": "Do not disturb",
            "OFFLINE_MESSAGE": "Offline",
            "LISTENING_MESSAGE": "Listening",
            "STREAMING_MESSAGE": "Streaming",
        }
        settings: dict[str, Any] | Any = await self.config.user(user=author).get_raw()
        for attr, name in data.items():
            if type(settings[attr]) in [tuple, list]:
                # This is just to keep backwards compatibility
                status_msg, delete_after = settings[attr]
            else:
                status_msg: Any = settings[attr]
                delete_after: None = None
            if settings[attr] and len(status_msg) > 20:
                status_msg: Any = status_msg[:20] + "..."
            if settings[attr] and len(status_msg) <= 1:
                status_msg = "True"
            if delete_after:
                msg += f"{name}: {status_msg} deleted after {delete_after}s\n"
            else:
                msg += f"{name}: {status_msg}\n"
        if "GAME_MESSAGE" in settings:
            if not settings["GAME_MESSAGE"]:
                games = "False"
            else:
                games = "True"
            msg += f"Games: {games}\n"
            for game in settings["GAME_MESSAGE"]:
                status_msg, delete_after = settings["GAME_MESSAGE"][game]
                if len(status_msg) > 20:
                    status_msg: Any = status_msg[:-20] + "..."
                if len(status_msg) <= 1:
                    status_msg = "True"
                if delete_after:
                    msg += f"{game}: {status_msg} deleted after {delete_after}s\n"
                else:
                    msg += f"{game}: {status_msg}\n"

        if ctx.channel.permissions_for(ctx.me).embed_links:
            em: discord.Embed = discord.Embed(description=msg[:2048], color=author.color)
            em.set_author(
                name=f"{author.display_name}'s away settings",
                icon_url=author.avatar.url,
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(content=f"{author.display_name} away settings\n" + msg)
