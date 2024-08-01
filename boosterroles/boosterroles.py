from typing import *

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu


class BoosterRoles(commands.Cog):
    """Gives custom roles to boosters"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 718395193090375700, force_registration=True)
        default_guild = {
            "state": True,
            "role_position": 0,
            "role_threshold": 1,
        }
        default_member = {
            "booster_role_level": 0,  # Number of boosts the member has
            "role_data": None,  # int of role
        }

        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not message.is_system():
            return

        if message.type == 8:
            if message.guild.system_channel == message.channel:
                booster_role_level = await self.config.member(
                    message.author
                ).booster_role_level()
                booster_role_level += 1

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if (
            before.guild.premium_subscriber_role not in after.roles
            and before.guild.premium_subscriber_role in before.roles
        ):
            # Remove priviliges when the user looses their booster role
            await self.config.member(before).booster_role_level().set(0)

    @commands.group()
    @checks.has_permissions(manage_guild=True)
    async def boosterroles(self, ctx: commands.Context):
        """Settings for the welcomer cog"""
        pass

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def state(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the BoosterRoles cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send(f"BoosterRoles state set to {state}")

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def position(self, ctx: commands.Context, position_or_id: int):
        """
        Set the position of the roles created by the BoosterRoles cog
        """
        if position_or_id > 10000:
            position = ctx.guild.get_role(position_or_id).position

        await self.config.guild(ctx.guild).role_position.set(position)
        await ctx.send(f"BoosterRoles position set to {position}")

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def threshold(self, ctx: commands.Context, threshold: int):
        """
        Set the threshold required to use custom roles
        """
        threshold = abs(threshold)
        await self.config.guild(ctx.guild).role_threshold.set(threshold)
        await ctx.send(f"BoosterRoles position set to {threshold}")

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def printdata(self, ctx: commands.Context, id: int = None):
        """Show all settings."""
        if id:
            member = ctx.guild.get_member(id)
        else:
            member = ctx.author
        data = await self.config.member(member).all()
        await menu(ctx, list(pagify(str(data), page_length=2000)))

    @boosterroles.command()
    async def resetme(self, ctx: commands.Context):
        """Reset your settings to the default values."""
        await self.config.member(ctx.message.author).clear()
        await ctx.send("Settings reset.")

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def clear(self, ctx: commands.Context):
        """Reset all settings to the default values."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Settings reset.")

    @boosterroles.group()
    async def roles(self, ctx: commands.Context):
        """Configure your booster role"""
        pass

    @roles.command()
    @commands.guild_only()
    # @commands.bot_has_permissions(manage_roles=True)
    async def name(self, ctx: commands.Context, name: str):
        """Set the name of your custom role"""
        role_id: Optional[int] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()

        role_position: int = await self.config.guild(ctx.guild).role_position()
        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=name,
                    reason="Booster Roles Cog",
                    color=discord.Color.pink(),
                    hoist=False,
                    mentionable=False,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(
                        name=name,
                    )
                    await ctx.send("Changed role name")
                except AttributeError:  # If the role is deleted after being set
                    role_position: Optional[int] = await self.config.guild(
                        ctx.guild
                    ).role_position()
                    role = await ctx.guild.create_role(
                        name=name,
                        reason="Booster Roles Cog",
                        color=discord.Color.pink(),
                        hoist=False,
                        mentionable=False,
                    )
                    await ctx.send("Done")

            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    # @commands.bot_has_permissions(manage_roles=True)
    async def color(self, ctx: commands.Context, color: str):
        """Set the color of your custom role"""
        role_id: Union[int | None] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()
        role_position: int = await self.config.guild(ctx.guild).role_position()
        try:
            color = discord.Color.from_str(color)
        except ValueError:
            await ctx.send(
                """Improper input. The following formats are accepted:\n- 0x<hex>\n- #<hex>\n- 0x#<hex>\n- "rgb(<number>, <number>, <number>)"

            Like CSS, <number> can be either 0-255 or 0-100% and <hex> can be either a 6 digit hex number or a 3 digit hex shortcut (e.g. #FFF).
            Replace <hex> or <number> with the actual values. The quotations are important in the RGB input to ensure correct parsing. Furthermore, #000000 or rgb(0,0,0) turns the role color invisible. For black use #000001 or rgb(1,1,1)
            """
            )
            return
        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name="Nitro Booster",
                    reason="Booster Roles Cog",
                    color=color,
                    hoist=False,
                    mentionable=False,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(color=color)
                    await ctx.send("Changed role color")
                except AttributeError:  # If the role is deleted after being set
                    role = await ctx.guild.create_role(
                        name="Nitro Booster",
                        reason="Booster Roles Cog",
                        color=color,
                        hoist=False,
                        mentionable=False,
                    )
                    await ctx.send("Done")

            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    # @commands.bot_has_permissions(manage_roles=True)
    async def icon(self, ctx: commands.Context):
        """Set the display icon of your role."""
        if "ROLE_ICONS" not in ctx.guild.features:
            await ctx.send(
                "Your guild does not support role icons due to its boost level."
            )
            return
        role_id: Union[int | None] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()

        role_position: int = await self.config.guild(ctx.guild).role_position()

        # Get the attached file and check its validity
        # Thanks Mr 42

        image = await ctx.message.attachments[0].read()
        if image == None:
            await ctx.send("Please attach an image to add as a role icon.")

        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name="Nitro Booster",
                    reason="Booster Roles Cog",
                    color=discord.Color.pink(),
                    display_icon=image,
                    hoist=False,
                    mentionable=False,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(display_icon=image)
                    await ctx.send("Changed role color")
                except AttributeError:  # If the role is deleted after being set
                    role = await ctx.guild.create_role(
                        name="Nitro Booster",
                        reason="Booster Roles Cog",
                        color=discord.Color.pink(),
                        display_icon=image,
                        hoist=False,
                        mentionable=False,
                    )
                    await ctx.send("Done")

            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.member)
    # @commands.bot_has_permissions(manage_roles=True)
    async def assign(self, ctx: commands.Context):
        """Assign / Unassign the booster role to yourself"""

        if ctx.guild.premium_subscriber_role in ctx.author.roles:
            role_threshold = await self.config.guild(ctx.guild).role_threshold()
            boosts = await self.config.guild(ctx.guild).role_threshold()

            if boosts >= role_threshold:
                role_data: int = await self.config.member(ctx.author).role_data()
                role = await ctx.guild.get_role(role_data)
                if not role:
                    role_position: int = await self.config.guild(
                        ctx.guild
                    ).role_position()

                    role = await ctx.guild.create_role(
                        name="Nitro Booster",
                        reason="Booster Roles Cog",
                        color=discord.Color.pink(),
                        hoist=False,
                        mentionable=False,
                    )

                    await ctx.send(
                        "Assigned the default role, please configure it to your liking."
                    )
                if role in ctx.author.roles:
                    await ctx.author.remove_roles(role, reason="Unassigned role")

    @roles.command()
    @commands.guild_only()
    @checks.has_permissions(manage_guild=True)
    async def set(self, ctx: commands.Context, user_id: int, boosts: int = 1):
        """Set the boosts of a user"""
        member = ctx.guild.get_member(user_id)
        await self.config.member(member).booster_role_level.set(abs(boosts))
