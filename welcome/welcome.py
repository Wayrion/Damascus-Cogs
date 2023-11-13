import discord
import asyncio
import time
import os
from contextlib import suppress
from redbot.core import Config, commands, checks
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import humanize_list, inline
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, UnidentifiedImageError
from string import Formatter
from typing import Optional

class Welcome(commands.Cog):
    """Welcomes a user to the server with an image."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 718395193090375700, force_registration=True)
        default_guild  = {
            'enabled': False,
            "avatar_border": 6,
            "avatar_border_color": (255, 255, 255),
            "avatar_pos": (550, 190),
            "avatar_radius": 128,
            "member_overlay_pos": (550, 368),
            "member_count_overlay_pos": (550, 416),
            "text_color": (255, 255, 255),
            "text_size": 46,
            "count_color": (180, 180, 180),
            "count_size": 38,
            "member_join_message": "Hello {member}, welcome to **{guild}**!",
            "member_leave_message": "**{member}** has left the server.",
            "member_join_roles": [],
            "join_channel": None,
            "join_image": True,
            "leave_channel": None,
            "leave_enabled": True,
            "leave_image": False,
        }
        self.config.register_guild(**default_guild)

    async def wait_for_onboarding(self, member:discord.Member):
        timeout = 300  # 5 minutes
        start_time = time.monotonic()

        while not member.flags.completed_onboarding:
            if time.monotonic() - start_time >= timeout:
                raise asyncio.TimeoutError("Timed out waiting for member to complete onboarding")
            await asyncio.sleep(5)
        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Welcomes a user to the server with an image."""
        if member.bot or not await self.config.guild(member.guild).enabled():
            return

        async with self.config.guild(member.guild).all() as settings:
            file = None
            if settings["join_image"]:
                msg = f"{member.name} just joined the server"
                background = await self.create_image(settings, member, msg)

                with BytesIO() as image_binary:
                    background.save(image_binary, format="png")
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename=f"welcome{member.id}.png")

            channel = None
            if settings["join_channel"]:
                channel = member.guild.get_channel(settings["join_channel"])
            elif member.guild.system_channel:
                channel =  member.guild.system_channel

            if channel:
                text = settings["member_join_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=channel)
                await channel.send(text, file=file)

            if settings["member_join_roles"]:
                try:
                    await asyncio.wait_for(self.wait_for_onboarding(member), timeout=300)
                    async with self.config.guild(member.guild).member_join_roles() as roles:
                        for role in roles:
                            await member.add_roles(member.guild.get_role(role))

                except asyncio.TimeoutError:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Sends a goodbye message with an image when a user leaves the server."""
        if member.bot or not await self.config.guild(member.guild).enabled() or not await self.config.guild(member.guild).leave_enabled():
            return

        async with self.config.guild(member.guild).all() as settings:
            file = None
            if settings["leave_image"]:
                msg = f"{member.name} left the server."
                background = await self.create_image(settings, member, msg)

                with BytesIO() as image_binary:
                    background.save(image_binary, format="png")
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename=f"goodbye{member.id}.png")

            channel = None
            if settings["leave_channel"]:
                channel = member.guild.get_channel(settings["leave_channel"])
            elif member.guild.system_channel:
                channel =  member.guild.system_channel

            if channel:
                text = settings["member_leave_message"].format(member=member.name)
                await channel.send(text, file=file)

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def welcomeset(self, ctx: commands.Context):
        """Settings for the welcomer cog"""
        pass

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def background(self, ctx: commands.Context):
        """Set or remove the background image for the welcome message."""
        if not ctx.message.attachments:
            if os.path.isfile(cog_data_path(self) / f"background-{ctx.guild.id}.png"):
                # Remove the file from the data folder
                os.remove(cog_data_path(self) / f"background-{ctx.guild.id}.png")
                await ctx.send("Background image has been removed.")
                return
            await ctx.send("Please attach an image file to set as the background.")
            return

        # Get the attached file and check its validity
        try:
            image = Image.open(BytesIO(await ctx.message.attachments[0].read()))
        except UnidentifiedImageError:
            await ctx.send("Please attach a valid image file.")
            return

        # Save the file to the data folder
        path = cog_data_path(self) / f"background-{ctx.guild.id}.png"
        image.save(path)

        # Send a message saying that the background was set
        await ctx.send("Background set to uploaded file.")

    @welcomeset.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar(self, ctx: commands.Context):
        """Avatar settings"""
        pass

    @avatar.command(name="border")
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_border(self, ctx: commands.Context, border: int):
        """Set the profile picture border width.
        Set to 0 to disable."""
        b = abs(border)
        await self.config.guild(ctx.guild).avatar_border.set(b)
        await ctx.send(f"Avatar border set to {b}.")

    @avatar.command(name="border_color")
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_border_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Set the profile picture border color using RGB values."""
        try:
            color = discord.Color.from_rgb(red, green, blue).to_rgb()
            await self.config.guild(ctx.guild).avatar_border_color.set(color)
            await ctx.send(f"Avatar border color set to {color}.")
        except ValueError:
            await ctx.send(f"Error setting avatar border color to {red}, {green}, {blue}.")

    @avatar.command(name="position")
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_pos(self, ctx: commands.Context, x: int, y: int):
        """Set the position of the profile picture."""
        await self.config.guild(ctx.guild).avatar_pos.set((x, y))
        await ctx.send(f"Member profile position set to ({x}, {y}).")

    @avatar.command(name="radius")
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_radius(self, ctx: commands.Context, radius: int):
        """Set the radius of the profile picture.
        Set to 0 to disable."""
        r = abs(radius)
        await self.config.guild(ctx.guild).avatar_radius.set(r)
        await ctx.send(f"Avatar radius set to {r}.")

    @welcomeset.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def channel(self, ctx: commands.Context):
        """Channel settings"""
        pass

    @channel.command(name="join")
    @checks.admin_or_permissions(manage_guild=True)
    async def join_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel to send the welcome message in."""
        await self.config.guild(ctx.guild).join_channel.set(channel.id)
        await ctx.send(f"Join channel set to {channel.mention}.")

    @channel.command(name="leave")
    @checks.admin_or_permissions(manage_guild=True)
    async def leave_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel to send the leave message in."""
        await self.config.guild(ctx.guild).leave_channel.set(channel.id)
        await ctx.send(f"Leave channel set to {channel.mention}.")

    @welcomeset.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def count(self, ctx: commands.Context):
        """Member counter settings"""
        pass

    @count.command(name="color")
    @checks.admin_or_permissions(manage_guild=True)
    async def count_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Set the color of the counter using RGB values."""
        try:
            color = discord.Color.from_rgb(red, green, blue).to_rgb()
            await self.config.guild(ctx.guild).count_color.set(color)
            await ctx.send(f"Count color set to {color}.")
        except ValueError:
            await ctx.send(f"Error setting count color to {red}, {green}, {blue}.")

    @count.command(name="position")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_count_overlay_pos(self, ctx: commands.Context, x: int, y: int):
        """Set the position of the member count overlay."""
        await self.config.guild(ctx.guild).member_count_overlay_pos.set((x, y))
        await ctx.send(f"Member count overlay position set to ({x}, {y}).")

    @count.command(name="size")
    @checks.admin_or_permissions(manage_guild=True)
    async def count_size(self, ctx: commands.Context, size: int):
        """Set the font size of the counter.
        Set to 0 to disable."""
        s = abs(size)
        await self.config.guild(ctx.guild).count_size.set(s)
        await ctx.send(f"Count size set to {s}.")

    @welcomeset.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def member(self, ctx: commands.Context):
        """Member overlay settings"""
        pass

    @welcomeset.command(name="join_image")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_join_image(self, ctx: commands.Context) -> None:
        """Enable or disable image when a member joins."""
        enabled = not await self.config.guild(ctx.guild).join_image()
        await self.config.guild(ctx.guild).join_image.set(enabled)

        action = "enabled" if enabled else "disabled"
        await ctx.send(f"Welcome image has been {action}.")

    @member.command(name="join_message")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_join_message(self, ctx: commands.Context, *, message: str):
        """Set the message to send when a member joins.
        Variables: {member}, {guild}, {guild_owner}, {channel}
        Example: `[p]welcomeset member join_message {member} joined {guild}! Welcome!`
        Variables in {} will be replaced with the appropriate value."""
        fail = []
        options = {'member', 'guild', 'guild_owner', 'channel'}
        for x in [i[1] for i in Formatter().parse(message) if i[1] is not None and i[1] not in options]:
            fail.append(inline(x))

        if fail:
            msg = "You are not allowed to use {key} in the message.".format(key=humanize_list(fail))
            await ctx.send(msg)
            return
        msg = message.replace("\\n", "\n").strip()
        await self.config.guild(ctx.guild).member_join_message.set(msg)
        await ctx.send(f"Member join message set to {msg}.")

    @member.command(name="join_roles")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_join_roles(self, ctx: commands.Context, *roles: discord.Role):
        """Set the roles to give to a member when they join."""
        await self.config.guild(ctx.guild).member_join_roles.set([role.id for role in roles])
        await ctx.send(f"Member join roles set to {[role.name for role in roles]}.")

    @member.command(name="leave_image")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_leave_image(self, ctx: commands.Context) -> None:
        """Enable or disable image when a member leaves."""
        enabled = not await self.config.guild(ctx.guild).leave_image()
        await self.config.guild(ctx.guild).leave_image.set(enabled)

        action = "enabled" if enabled else "disabled"
        await ctx.send(f"Member leave image has been {action}.")

    @member.command(name="leave_message")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_leave_message(self, ctx: commands.Context, *, message: str):
        """Set the message to send when a member leaves.
        Variables: {member}
        Example: `[p]welcomeset member leave_message {member} left! Goodbye!`
        Variables in {} will be replaced with the appropriate value."""
        fail = []
        options = {'member'}
        for x in [i[1] for i in Formatter().parse(message) if i[1] is not None and i[1] not in options]:
            fail.append(inline(x))

        if fail:
            msg = "You are not allowed to use {key} in the message.".format(key=humanize_list(fail))
            await ctx.send(msg)
            return
        msg = message.replace("\\n", "\n").strip()
        await self.config.guild(ctx.guild).member_leave_message.set(msg)
        await ctx.send(f"Member leave message set to {msg}.")

    @member.command(name="leave_toggle")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_leave_toggle(self, ctx: commands.Context) -> None:
        """Enable or disable the leave message altogether."""
        enabled = not await self.config.guild(ctx.guild).leave_enabled()
        await self.config.guild(ctx.guild).leave_enabled.set(enabled)

        action = "enabled" if enabled else "disabled"
        await ctx.send(f"Member leave message has been {action}.")

    @welcomeset.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def text(self, ctx: commands.Context):
        """Member overlay settings"""
        pass

    @text.command(name="color")
    @checks.admin_or_permissions(manage_guild=True)
    async def text_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Set the color of the text using RGB values."""
        try:
            color = discord.Color.from_rgb(red, green, blue).to_rgb()
            await self.config.guild(ctx.guild).text_color.set(color)
            await ctx.send(f"Text color set to {color}.")
        except ValueError:
            await ctx.send(f"Error setting text color to {red}, {green}, {blue}.")

    @text.command(name="position")
    @checks.admin_or_permissions(manage_guild=True)
    async def member_overlay_pos(self, ctx: commands.Context, x: int, y: int):
        """Set the position of the member joined overlay."""
        await self.config.guild(ctx.guild).member_overlay_pos.set((x, y))
        await ctx.send(f"Member overlay position set to ({x}, {y}).")

    @text.command(name="size")
    @checks.admin_or_permissions(manage_guild=True)
    async def text_size(self, ctx: commands.Context, size: int):
        """Set the font size of the text.
        Set to 0 to disable."""
        s = abs(size)
        await self.config.guild(ctx.guild).text_size.set(s)
        await ctx.send(f"Text size set to {s}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context) -> None:
        """Enable or disable this cog in the current guild."""
        enabled = not await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(enabled)

        action = "enabled" if enabled else "disabled"
        await ctx.send(f"Welcome has been {action}.")


    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def test(self, ctx: commands.Context, member: Optional[discord.Member]):
        """Send a test message in the current channel."""
        if not member:
            member = ctx.author

        async with self.config.guild(member.guild).all() as settings:
            file = None
            if settings["join_image"]:
                msg = f"{member.name} just joined the server"
                background = await self.create_image(settings, member, msg)

                with BytesIO() as image_binary:
                    background.save(image_binary, format="png")
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename=f"welcome{member.id}.png")

            await ctx.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=ctx.channel), file=file)

    async def create_image(self, settings: dict, member: discord.Member, msg: str) -> Image.Image:
        # Use PIL and overlay the background on the profile picture at the specified coordinates
        if os.path.isfile(cog_data_path(self) / f"background-{member.guild.id}.png"):
            path = cog_data_path(self) / f"background-{member.guild.id}.png"
            background = Image.open(path)
            img = ImageDraw.Draw(background)
        else:
            background = Image.new(mode="RGBA", size=(1100, 500), color=(23, 24, 30))
            img = ImageDraw.Draw(background)
            img.rectangle([(55, 25), (1045, 475)], fill=(0, 0, 0))

        if settings["avatar_border"] > 0 and settings["avatar_radius"] > 0:
            r = settings["avatar_radius"] + settings["avatar_border"]
            img.ellipse((settings["avatar_pos"][0]-r, settings["avatar_pos"][1]-r, settings["avatar_pos"][0]+r, settings["avatar_pos"][1]+r), fill=tuple(settings["avatar_border_color"]))

        if (r := settings["avatar_radius"]) > 0:
            mask = Image.new("L", (r*2, r*2), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, r*2, r*2), fill=255)

            profile = Image.open(BytesIO(await member.avatar.read()))
            profile = profile.resize((r*2, r*2))

            # Create a new image with a white background
            circle_image = Image.new("RGBA", (r*2, r*2), (255, 255, 255, 0))

            # Draw a circle on the new image
            draw = ImageDraw.Draw(circle_image)
            draw.ellipse((0, 0, r*2, r*2), fill=(255, 255, 255, 255))

            # Use the circle image as a mask for the profile image
            profile = Image.composite(profile, circle_image, circle_image)

            # Paste the profile image onto the background at the specified position
            val = (settings["avatar_pos"][0] - r, settings["avatar_pos"][1] - r)
            background.paste(profile, val, profile)

        if (size := settings["text_size"]) > 0:
            draw = ImageDraw.Draw(background)
            draw.text(settings["member_overlay_pos"], msg, tuple(settings["text_color"]), font=ImageFont.load_default(size=size), anchor="mm")

        if (size := settings["count_size"]) > 0:
            draw = ImageDraw.Draw(background)
            draw.text(settings["member_count_overlay_pos"], f"Member #{member.guild.member_count}", tuple(settings["count_color"]), font=ImageFont.load_default(size=size), anchor="mm")
        return background

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def reset(self, ctx: commands.Context):
        """Reset all settings to the default values."""
        await self.config.guild(ctx.guild).clear()
        with suppress(FileNotFoundError):
            os.remove(cog_data_path(self) / f"background-{ctx.guild.id}.png")
        await ctx.send("Settings reset.")
