import discord
import os
from contextlib import suppress
from redbot.core import Config, commands, checks
from redbot.core.data_manager import cog_data_path
from typing import Optional, Dict, List


class Notifier(commands.Cog):
    """Welcomes a user to the server with an image."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 718395193090375700, force_registration=True)
        default_guild = {
            "annoucement_registry": {},  # Contains a dict of items where the name of the system message is the key and the role is the value
            "annoucement_channel": "",
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return

        guild_group = self.config.guild(message.guild)

        async with guild_group.annoucement_registry() as annoucement_registry:

            try:
                role = annoucement_registry[message.author.name]
            except KeyError:
                return

            await message.channel.send(
                f"<@&{role}>",
                allowed_mentions=discord.AllowedMentions(users=True, roles=True),
            )

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def notifierset(self, ctx: commands.Context):
        """Settings for the welcomer cog"""
        pass

    @notifierset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def addrole(self, ctx: commands.Context, name: str, role: int):
        """Add the <role> to ping when an annoucement from a <name> is made"""
        guild_group = self.config.guild(ctx.guild)

        annoucement_registry: Dict
        async with guild_group.annoucement_registry() as annoucement_registry:
            annoucement_registry.update({name: role})

        await ctx.send(f"Set to ping <@&{role}>, when {name} makes an annoucement.")

    @notifierset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def removerole(self, ctx: commands.Context, name: str, role: int):
        """Remove the <role> to ping when an annoucement from a <name> is made"""
        guild_group = self.config.guild(ctx.guild)
        annoucement_registry: Dict
        async with guild_group.annoucement_registry() as annoucement_registry:
            try:
                del annoucement_registry[name]
            except:
                pass

        await ctx.send(f"Removed <@&{role}> mention, when {name} makes an annoucement.")

    @notifierset.command()
    @commands.is_owner()
    async def nukeconfig(self, ctx):
        """Nuke the config"""
        await self.config.clear_all()
        await ctx.send("Nuked the config")
