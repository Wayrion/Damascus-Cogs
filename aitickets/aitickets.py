import asyncio
import datetime
import logging
import typing as t
from logging import Logger
from time import perf_counter
from typing import Literal

import discord
from discord import Guild, Member, Thread
from discord.abc import GuildChannel
from discord.ext import tasks
from discord.ui import View
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n

from .abc import CompositeMetaClass
from .commands import TicketCommands
from .common.constants import DEFAULT_GLOBAL, DEFAULT_GUILD
from .common.functions import Functions
from .common.utils import (
    close_ticket,
    prune_invalid_tickets,
    ticket_owner_hastyped,
    update_active_overview,
)
from .common.views import CloseView, LogView, PanelView

log: Logger = logging.getLogger(name="red.wayrion.aitickets")
_ = Translator(name="Tickets", file_location=__file__)


# redgettext -D aitickets.py commands/base.py commands/admin.py common/views.py common/menu.py common/utils.py
@cog_i18n(translator=_)
class Tickets(TicketCommands, Functions, commands.Cog, metaclass=CompositeMetaClass):
    """
    Support ticket system with multi-panel functionality
    """

    __author__ = "[wayrion](https://github.com/wayrion/Damascus-cogs)"
    __version__ = "2.9.15"

    def format_help_for_context(self, ctx) -> str:
        helpcmd: str = super().format_help_for_context(ctx)
        info: str = (
            f"{helpcmd}\nCog Version: {self.__version__}\nAuthor: {self.__author__}\n"
        )
        return info

    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        """No data to delete"""
        return

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=1368567270300975227, force_registration=True
        )
        self.config.register_guild(**DEFAULT_GUILD)
        self.config.register_global(**DEFAULT_GLOBAL)

        # Cache
        self.valid: list[discord.abc.Messageable] = []  # Valid ticket channels
        self.views: list[discord.ui.View] = []  # Saved views to end on reload
        self.view_cache: t.Dict[
            int, t.List[discord.ui.View]
        ] = {}  # Saved views to end on reload
        self.initializing = False

        self.auto_close.start()

    async def cog_load(self) -> None:
        asyncio.create_task(coro=self._startup())

    async def cog_unload(self) -> None:
        self.auto_close.cancel()
        for view in self.views:
            view.stop()

    async def _startup(self) -> None:
        await self.bot.wait_until_red_ready()
        await asyncio.sleep(6)
        await self.initialize()

    async def initialize(self, target_guild: discord.Guild | None = None) -> None:
        if target_guild:
            data = await self.config.guild(guild=target_guild).all()
            return await self._init_guild(guild=target_guild, data=data)

        t1: float = perf_counter()
        conf: dict = await self.config.all_guilds()
        for gid, data in conf.items():
            if not data:
                continue
            guild: Guild | None = self.bot.get_guild(gid)
            if not guild:
                continue
            try:
                await self._init_guild(guild, data)
            except Exception as e:
                log.error(
                    msg=f"Failed to initialize tickets for {guild.name}", exc_info=e
                )

        td: float = (perf_counter() - t1) * 1000
        log.info(msg=f"Tickets initialized in {round(number=td, ndigits=1)}ms")

    async def _init_guild(self, guild: discord.Guild, data: dict) -> None:
        # Stop and clear guild views from cache
        views: list[View] = self.view_cache.setdefault(guild.id, [])
        for view in views:
            view.stop()
        self.view_cache[guild.id].clear()

        pruned: bool = await prune_invalid_tickets(guild, conf=data, config=self.config)
        if pruned:
            data: dict = await self.config.guild(guild).all()

        # Refresh overview panel
        new_id: int | None = await update_active_overview(guild, conf=data)
        if new_id:
            await self.config.guild(guild).overview_msg.set(value=new_id)

        # v1.14.0 Migration, new support role schema
        cleaned: list = []
        for i in data["support_roles"]:
            if isinstance(i, int):
                cleaned.append([i, False])
        if cleaned:
            await self.config.guild(guild).support_roles.set(value=cleaned)

        # Refresh buttons for all panels
        migrations = False
        all_panels = data["panels"]
        prefetched: list = []
        to_deploy: dict = {}  # Message ID keys for multi-button support
        for panel_name, panel in all_panels.items():
            category_id = panel["category_id"]
            channel_id = panel["channel_id"]
            message_id = panel["message_id"]
            if any([not category_id, not channel_id, not message_id]):
                # Panel does not have all channels set
                continue

            category = guild.get_channel(category_id)
            channel_obj = guild.get_channel(channel_id)
            if isinstance(channel_obj, discord.ForumChannel) or isinstance(
                channel_obj, discord.CategoryChannel
            ):
                log.error(
                    msg=f"Invalid channel type for panel {panel_name} in {guild.name}"
                )
                continue
            if any([not category, not channel_obj]):
                if not category:
                    log.error(
                        msg=f"Invalid category for panel {panel_name} in {guild.name}"
                    )
                if not channel_obj:
                    log.error(
                        msg=f"Invalid channel for panel {panel_name} in {guild.name}"
                    )
                continue

            if message_id not in prefetched:
                try:
                    await channel_obj.fetch_message(message_id)
                    prefetched.append(message_id)
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    log.error(
                        msg=f"I can no longer see the {panel_name} panel's channel in {guild.name}"
                    )
                    continue

            # v1.3.10 schema update (Modals)
            if "modals" not in panel:
                panel["modals"] = {}
                migrations = True
            # Schema update (Sub support roles)
            if "roles" not in panel:
                panel["roles"] = []
                migrations = True
            # v1.14.0 Schema update (Mentionable support roles + alt channel)
            cleaned = []
            for i in panel["roles"]:
                if isinstance(i, int):
                    cleaned.append([i, False])
            if cleaned:
                panel["roles"] = cleaned
                migrations = True
            if "alt_channel" not in panel:
                panel["alt_channel"] = 0
                migrations = True
            # v1.15.0 schema update (Button priority and rows)
            if "row" not in panel or "priority" not in panel:
                panel["row"] = None
                panel["priority"] = 1
                migrations = True
            # v2.4.0 schema update (Disable panels)
            if "disabled" not in panel:
                panel["disabled"] = False
                migrations = True

            panel["name"] = panel_name
            key: str = f"{channel_id}-{message_id}"
            if key in to_deploy:
                to_deploy[key].append(panel)
            else:
                to_deploy[key] = [panel]

        if not to_deploy:
            return

        # Update config for any migrations
        if migrations:
            await self.config.guild(guild).panels.set(value=all_panels)

        try:
            for panels in to_deploy.values():
                sorted_panels: list = sorted(panels, key=lambda x: x["priority"])
                panelview: PanelView = PanelView(
                    bot=self.bot, guild=guild, config=self.config, panels=sorted_panels
                )
                # Panels can change so we want to edit every time
                await panelview.start()
                self.view_cache[guild.id].append(panelview)
        except discord.NotFound:
            log.warning(msg=f"Failed to refresh panels in {guild.name}")

        # Refresh view for logs of opened tickets (v1.8.18 update)
        for uid, opened_tickets in data["opened"].items():
            member = guild.get_member(int(uid))
            if not member:
                continue
            for ticket_channel_id, ticket_info in opened_tickets.items():
                ticket_channel = guild.get_channel_or_thread(int(ticket_channel_id))
                if not ticket_channel:
                    continue

                # v2.0.0 stores message id for close button to re-init views on reload
                if message_id := ticket_info.get("message_id"):
                    view = CloseView(self.bot, self.config, int(uid), ticket_channel)
                    self.bot.add_view(view, message_id=message_id)
                    self.view_cache[guild.id].append(view)

                if not ticket_info["logmsg"]:
                    continue

                panel_name = ticket_info["panel"]
                if panel_name not in all_panels:
                    continue
                panel = all_panels[panel_name]
                if not panel["log_channel"]:
                    continue
                log_channel = guild.get_channel(int(panel["log_channel"]))
                if not log_channel:
                    log.warning(
                        msg=f"Log channel no longer exits for {member.name}'s ticket in {guild.name}"
                    )
                    continue

                max_claims = ticket_info.get("max_claims", 0)
                logview = LogView(guild, ticket_channel, max_claims)
                self.bot.add_view(logview, message_id=ticket_info["logmsg"])
                self.view_cache[guild.id].append(logview)

    @tasks.loop(minutes=20)
    async def auto_close(self) -> None:
        actasks: list = []
        conf: dict = await self.config.all_guilds()
        for gid, conf in conf.items():
            if not conf:
                continue
            guild: Guild | None = self.bot.get_guild(gid)
            if not guild:
                continue
            inactive = conf["inactive"]
            if not inactive:
                continue
            opened = conf["opened"]
            if not opened:
                continue
            for uid, tickets in opened.items():
                member: Member | None = guild.get_member(int(uid))
                if not member:
                    continue
                for channel_id, ticket in tickets.items():
                    has_response = ticket.get("has_response")
                    if has_response and channel_id not in self.valid:
                        self.valid.append(channel_id)
                        continue
                    if channel_id in self.valid:
                        continue
                    channel: GuildChannel | Thread | None = guild.get_channel_or_thread(
                        int(channel_id)
                    )
                    if not channel:
                        continue
                    now: datetime = datetime.datetime.now().astimezone()
                    opened_on: datetime = datetime.datetime.fromisoformat(
                        ticket["opened"]
                    )
                    hastyped: bool = await ticket_owner_hastyped(channel, member)
                    if hastyped and channel_id not in self.valid:
                        self.valid.append(channel_id)
                        continue
                    td: float = (now - opened_on).total_seconds() / 3600
                    next_td = td + 0.33
                    if td < inactive <= next_td:
                        # Ticket hasn't expired yet but will in the next loop
                        warning: str = _(
                            untranslated="If you do not respond to this ticket "
                            "within the next 20 minutes it will be closed automatically."
                        )
                        await channel.send(f"{member.mention}\n{warning}")
                        continue
                    elif td < inactive:
                        continue

                    time: Literal["hours", "hour"] = (
                        "hours" if inactive != 1 else "hour"
                    )
                    try:
                        await close_ticket(
                            bot=self.bot,
                            member=member,
                            guild=guild,
                            channel=channel,
                            conf=conf,
                            reason=_(
                                untranslated="(Auto-Close) Opened ticket with no response for "
                            )
                            + f"{inactive} {time}",
                            closedby=self.bot.user.name,
                            config=self.config,
                        )
                        log.info(
                            msg=f"Ticket opened by {member.name} has been auto-closed.\n"
                            f"Has typed: {hastyped}\n"
                            f"Hours elapsed: {td}"
                        )
                    except Exception as e:
                        log.error(
                            msg=f"Failed to auto-close ticket for {member} in {guild.name}\nException: {e}"
                        )

        if tasks:
            await asyncio.gather(*actasks)

    @auto_close.before_loop
    async def before_auto_close(self) -> None:
        await self.bot.wait_until_red_ready()
        await asyncio.sleep(300)

    # Will automatically close/cleanup any tickets if a member leaves that has an open ticket
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if not member:
            return
        guild: Guild = member.guild
        if not guild:
            return
        conf = await self.config.guild(guild).all()
        opened = conf["opened"]
        if str(member.id) not in opened:
            return
        tickets = opened[str(member.id)]
        if not tickets:
            return

        for cid in tickets:
            chan: GuildChannel | Thread | None = guild.get_channel_or_thread(int(cid))
            if not chan:
                continue
            try:
                await close_ticket(
                    bot=self.bot,
                    member=member,
                    guild=guild,
                    channel=chan,
                    conf=conf,
                    reason=_(untranslated="User left guild(Auto-Close)"),
                    closedby=self.bot.user.name,
                    config=self.config,
                )
            except Exception as e:
                log.error(
                    msg=f"Failed to auto-close ticket for {member} leaving {member.guild}\nException: {e}"
                )

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        if not thread:
            return
        guild: Guild = thread.guild
        conf = await self.config.guild(guild).all()
        pruned: bool = await prune_invalid_tickets(guild, conf, config=self.config)
        if pruned:
            log.info(msg="Pruned old ticket threads")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        if not channel:
            return
        guild: Guild = channel.guild
        conf = await self.config.guild(guild).all()
        pruned: bool = await prune_invalid_tickets(guild, conf, config=self.config)
        if pruned:
            log.info(msg="Pruned old ticket channels")
