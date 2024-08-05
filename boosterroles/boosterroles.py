import asyncio
from typing import *

import discord
from tabulate import tabulate
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
            "role_position": 1,
            "role_threshold": 1,
            "default_name": "Nitro Booster",
            "default_color": "#000001",
            "default_hoist": False,
            "default_mentionable": False,
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

        # if message.type == 8:
        if message.guild.system_channel == message.channel:
            booster_role_level = await self.config.member(
                message.author
            ).booster_role_level()
            booster_role_level += 1
            await self.config.member(message.author).booster_role_level.set(
                booster_role_level
            )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if (
            before.guild.premium_subscriber_role not in after.roles
            and before.guild.premium_subscriber_role in before.roles
        ):
            await self.config.member(before).booster_role_level.set(0)
            # Get and remove their custom role when they stop boosting
            role_data = await self.config.member(before).role_data()
            role = before.guild.get_role(role_data)
            try:
                # Remove priviliges when the user looses their booster role
                await role.delete()
            except:
                pass

            await self.config.member(before).role_data.set(None)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.config.member(member).booster_role_level.set(0)
        # Get and remove their custom role when they stop boosting
        role_data = await self.config.member(member).role_data()
        role = member.guild.get_role(role_data)
        try:
            # Remove priviliges when the user looses their booster role
            await role.delete()
        except:
            pass

        await self.config.member(member).role_data.set(None)

    @commands.group()
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
    async def position(self, ctx: commands.Context, role_id: int):
        """
        Set the role below which the booster roles will be created. The role is created above the role specified.
        """

        pos = ctx.guild.get_role(role_id).position

        await self.config.guild(ctx.guild).role_position.set(pos)
        await ctx.send(f"BoosterRoles position set to {pos}")

    @boosterroles.command()
    @checks.has_permissions(manage_guild=True)
    async def threshold(self, ctx: commands.Context, threshold: int):
        """
        Set the threshold required to use custom roles
        """
        threshold = abs(threshold)
        await self.config.guild(ctx.guild).role_threshold.set(threshold)
        await ctx.send(f"BoosterRoles position set to {threshold}")

    @boosterroles.group()
    @checks.has_permissions(manage_guild=True)
    async def default(self, ctx: commands.Context):
        """Set the default values"""
        pass

    @default.command()
    @checks.has_permissions(manage_guild=True)
    async def default_name(self, ctx: commands.Context, *, name: str):
        """
        Set the default name of the custom roles
        """

        await self.config.guild(ctx.guild).default_name.set(name)
        await ctx.send(f"BoosterRoles default name set to {name}")

    @default.command()
    @checks.has_permissions(manage_guild=True)
    async def default_color(self, ctx: commands.Context, color: str):
        """
        Set the default color of the custom roles.
        """

        await self.config.guild(ctx.guild).default_color.set(color)
        await ctx.send(f"BoosterRoles default color set to {color}")

    @default.command()
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
    @checks.has_permissions(manage_guild=True)
    async def clear(self, ctx: commands.Context):
        """Reset all settings to the default values for this guild. (Guild clear)"""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Settings reset.")

    @boosterroles.command()
    @checks.is_owner()
    async def nukeconfig(self, ctx: commands.Context):
        """Clear ALLLLLLLLL the data from config (Global clear)"""
        await self.config.clear_all()
        await ctx.send("Nuked the config")

    @boosterroles.group()
    async def roles(self, ctx: commands.Context):
        """Configure your booster role"""
        pass

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 360, commands.BucketType.guild)
    async def name(self, ctx: commands.Context, *, name):
        """Set the name of your custom role"""
        role_id: Optional[int] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()

        role_position = int(await self.config.guild(ctx.guild).role_position())
        default_name = await self.config.guild(ctx.guild).default_name()
        default_color = await self.config.guild(ctx.guild).default_color()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=name,
                    reason="Booster Roles Cog",
                    color=default_color,
                    hoist=default_hoist,
                    mentionable=default_mentionable,
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
                        color=default_color,
                        hoist=default_hoist,
                        mentionable=default_mentionable,
                    )
                    await ctx.send("Done")

            await asyncio.sleep(5)
            await role.edit(position=role_position)
            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 360, commands.BucketType.guild)
    async def color(self, ctx: commands.Context, color: str):
        """Set the color of your custom role"""
        role_id: Union[int | None] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()
        role_position = int(await self.config.guild(ctx.guild).role_position())
        default_name = await self.config.guild(ctx.guild).default_name()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        if color.lower() == "random":
            color = discord.Color.random()
        else:
            try:
                color = discord.Color.from_str(color)
            except ValueError:
                embed = discord.Embed(
                    title="Error: Improper Input",
                    description="""The following formats are accepted:\n- 0x<hex>\n- #<hex>\n- 0x#<hex>\n- "rgb(<number>, <number>, <number>)"\n- "random" for random color
                    Like CSS, <number> can be either 0-255 or 0-100% and <hex> can be either a 6 digit hex number or a 3 digit hex shortcut (e.g. #FFF).
                    Replace <hex> or <number> with the actual values. The quotations are important in the RGB input to ensure correct parsing. Furthermore, #000000 or rgb(0,0,0) turns the role color invisible. For black use #000001 or rgb(1,1,1)
                    """,
                    color=color,
                )
                await ctx.send(embed=embed)
                return
        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=default_name,
                    reason="Booster Roles Cog",
                    color=color,
                    hoist=default_hoist,
                    mentionable=default_mentionable,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(color=color)
                    await ctx.send("Changed role color")
                except AttributeError:  # If the role is deleted after being set
                    role = await ctx.guild.create_role(
                        name=default_name,
                        reason="Booster Roles Cog",
                        color=color,
                        hoist=default_hoist,
                        mentionable=default_mentionable,
                    )
                    await ctx.send("Done")

            await asyncio.sleep(5)
            await role.edit(position=role_position)
            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 360, commands.BucketType.guild)
    async def hoist(self, ctx: commands.Context, true_or_false: bool):
        """Set wether to hoist your role or not"""
        role_id: Union[int | None] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()
        role_position = int(await self.config.guild(ctx.guild).role_position())

        default_name = await self.config.guild(ctx.guild).default_name()
        default_color = await self.config.guild(ctx.guild).default_color()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=default_name,
                    reason="Booster Roles Cog",
                    color=default_color,
                    hoist=true_or_false,
                    mentionable=default_mentionable,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(hoist=true_or_false)
                    await ctx.send(f"Changed hoist to {true_or_false}")
                except AttributeError:  # If the role is deleted after being set
                    role = await ctx.guild.create_role(
                        name=default_name,
                        reason="Booster Roles Cog",
                        color=default_color,
                        hoist=true_or_false,
                        mentionable=default_mentionable,
                    )
                    await ctx.send("Done")

            await asyncio.sleep(5)
            await role.edit(position=role_position)
            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 360, commands.BucketType.guild)
    async def mentionable(self, ctx: commands.Context, true_or_false: bool):
        """Set wether to your role is mentionable or not"""
        role_id: Union[int | None] = await self.config.member(
            ctx.guild.get_member(ctx.author.id)
        ).role_data()
        role_position = int(await self.config.guild(ctx.guild).role_position())

        default_name = await self.config.guild(ctx.guild).default_name()
        default_color = await self.config.guild(ctx.guild).default_color()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=default_name,
                    reason="Booster Roles Cog",
                    color=default_color,
                    hoist=default_hoist,
                    mentionable=true_or_false,
                )
                await ctx.send("Done")

            else:
                try:
                    role = ctx.guild.get_role(role_id)
                    await role.edit(mentionable=true_or_false)
                    await ctx.send(f"Changed mentionable to {true_or_false}")
                except AttributeError:  # If the role is deleted after being set
                    role = await ctx.guild.create_role(
                        name=default_name,
                        reason="Booster Roles Cog",
                        color=default_color,
                        hoist=default_hoist,
                        mentionable=true_or_false,
                    )
                    await ctx.send("Done")

            await asyncio.sleep(5)
            await role.edit(position=role_position)
            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 360, commands.BucketType.guild)
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

        role_position = int(await self.config.guild(ctx.guild).role_position())

        # Get the attached file and check its validity
        # Thanks Mr 42

        image = await ctx.message.attachments[0].read()
        if image == None:
            await ctx.send("Please attach an image to add as a role icon.")

        default_name = await self.config.guild(ctx.guild).default_name()
        default_color = await self.config.guild(ctx.guild).default_color()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        try:
            if not role_id:
                role = await ctx.guild.create_role(
                    name=default_name,
                    reason="Booster Roles Cog",
                    color=default_color,
                    display_icon=image,
                    hoist=default_hoist,
                    mentionable=default_mentionable,
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
                        hoist=default_hoist,
                        mentionable=default_mentionable,
                    )
                    await ctx.send("Done")
            await asyncio.sleep(5)
            await role.edit(position=role_position)
            await self.config.member(ctx.author).role_data.set(role.id)

        except discord.Forbidden:
            await ctx.send(
                "I do not have enough permissions / role heirarchy to change your role. Please contact the bot owner."
            )

    @roles.command()
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def assign(self, ctx: commands.Context):
        """Assign / Unassign the booster role to yourself"""

        # if ctx.guild.premium_subscriber_role in ctx.author.roles:
        role_threshold = await self.config.guild(ctx.guild).role_threshold()
        boosts = await self.config.member(ctx.author).booster_role_level()
        role_position = int(await self.config.guild(ctx.guild).role_position())
        default_name = await self.config.guild(ctx.guild).default_name()
        default_color = await self.config.guild(ctx.guild).default_color()
        default_hoist = await self.config.guild(ctx.guild).default_hoist()
        default_mentionable = await self.config.guild(ctx.guild).default_mentionable()

        try:
            default_color = discord.Color.from_str(default_color)
        except ValueError:
            default_color = discord.Color.pink()

        if boosts >= role_threshold:
            role_data = await self.config.member(ctx.author).role_data()

            if not role_data:
                role = await ctx.guild.create_role(
                    name=default_name,
                    reason="Booster Roles Cog",
                    color=default_color,
                    hoist=default_hoist,
                    mentionable=default_mentionable,
                )

                await ctx.send(
                    "Assigned the default role, please configure it to your liking."
                )
                if role_position:
                    await asyncio.sleep(3)
                    await role.edit(position=role_position)
                await ctx.author.add_roles(role)
                await self.config.member(ctx.author).role_data.set(role.id)
            else:
                try:
                    await self.config.member(ctx.author).role_data.set(None)
                    role = ctx.guild.get_role(role_data)
                    await role.delete()
                    await ctx.send("Removed the custom role")
                except:
                    pass

    @roles.command()
    @commands.guild_only()
    @checks.is_owner()
    async def cleanup(self, ctx: commands.Context):
        """Delete all booster roles"""
        for member in ctx.guild.premium_subscribers:
            await self.config.member(member).booster_role_level.set(0)
            # Get and remove their custom role when they stop boosting
            role_data = await self.config.member(member).role_data()
            role = member.guild.get_role(role_data)
            try:
                # Remove priviliges when the user looses their booster role
                await role.delete()
            except:
                pass

            await self.config.member(member).role_data.set(None)
        await ctx.send("Done")

    @boosterroles.command()
    @commands.guild_only()
    @checks.has_permissions(manage_guild=True)
    async def list(self, ctx: commands.Context):
        """List all the roles and which users they belong to"""
        message = "```"
        table = []
        headers = ["User ID", "Role ID", "Boost Level"]
        default_color = await self.config.guild(ctx.guild).default_color()

        for member in ctx.guild.premium_subscribers:
            role_data = await self.config.member(member).role_data()
            booster_role_level = await self.config.member(member).booster_role_level()
            table.append([member.id, f"{role_data}", f"{booster_role_level}"])
        message += tabulate(table, headers=headers, tablefmt="github")
        message += "```"
        await ctx.send(embed=discord.Embed(title="Booster roles", description=message))

    @roles.command()
    @commands.guild_only()
    @checks.has_permissions(manage_guild=True)
    async def set(self, ctx: commands.Context, user_id: int, boosts: int = 1):
        """Set the boosts of a user"""
        member = ctx.guild.get_member(user_id)
        await self.config.member(member).booster_role_level.set(abs(boosts))
        await ctx.send(f"Set member's boost level to {abs(boosts)}")

    @roles.command()
    @commands.guild_only()
    async def resetme(self, ctx: commands.Context):
        """Reset your settings to the default values."""
        await self.config.member(ctx.message.author).clear()
        await ctx.send("Settings reset.")
