import discord
import asyncio
import time
import os
from contextlib import suppress
from redbot.core import Config, commands, checks
from redbot.core.data_manager import bundled_data_path, cog_data_path
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from typing import Optional

class Welcome(commands.Cog):
    """Welcomes a user to the server with an image."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 718395193090375700, force_registration=True)
        default_guild  = {
            "avatar_radius": 127,
            "avatar_border": 6,
            "avatar_border_color": (255, 255, 255),
            "avatar_pos": (550, 189),
            "member_count_overlay": True,
            "member_joined_overlay": True,
            "member_joined_overlay_pos": (550, 350),
            "member_count_overlay_pos": (550, 400),
            "text_size": 40,
            "count_size": 30,
            "text_color": (255, 255, 255),
            "count_color": (180, 180, 180),
            "member_leave_overlay": True,
            "member_join_message": "Welcome {member} to {guild}!",
            "member_leave_message": "Goodbye {member}!",
            "member_join_roles": [],
            "join_channel": None,
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
        if member.bot:
            return

        async with self.config.guild(member.guild).all() as settings:
            msg = f"{member.name} joined the server!"
            background = await self.create_image(settings, member, msg)

            with BytesIO() as image_binary:
                background.save(image_binary, format="png")
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename=f"welcome{member.id}.png")

            if settings["join_channel"]:
                channel = member.guild.get_channel(settings["join_channel"])
                await channel.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=channel), file=file)

            else:
                await member.guild.system_channel.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name), file=file)

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
        if member.bot:
            return

        async with self.config.guild(member.guild).all() as settings:
            msg = f"{member.name} left the server."
            background = await self.create_image(settings, member, msg)

            with BytesIO() as image_binary:
                background.save(image_binary, format="png")
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename=f"goodbye{member.id}.png")

            if settings["join_channel"]:
                channel = member.guild.get_channel(settings["join_channel"])
                await channel.send(settings["member_leave_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=channel), file=file)

            else:
                await member.guild.system_channel.send(settings["member_leave_message"].format(member=member.mention, guild=member.guild.name), file=file)

    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def welcomeset(self, ctx: commands.Context):
        """Settings for the welcomer cog"""
        pass

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def background(self, ctx: commands.Context):
        """Sets or removes the background image for the welcome message."""
        if not ctx.message.attachments:
            if os.path.isfile(cog_data_path(self) / f"background-{ctx.guild.id}.png"):
                # Remove the file from the data folder
                os.remove(cog_data_path(self) / f"background-{ctx.guild.id}.png")
                await ctx.send("Background image has been removed.")
                return
            await ctx.send("Please attach an image file to set as the background.")
            return

        # Get the attached file
        file = ctx.message.attachments[0]

        # Check if the attached file is an image
        if not file.filename.endswith((".png", ".jpg", ".jpeg")):
            await ctx.send("Please attach a PNG or JPEG image file.")
            return

        # Save the file to the data folder
        path = cog_data_path(self) / f"background-{ctx.guild.id}.png"
        await file.save(path)

        # Send a message saying that the background was set
        await ctx.send(f"Background set to {file.filename}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_radius(self, ctx: commands.Context, r: int):
        """Sets the radius of the profile picture."""
        await self.config.guild(ctx.guild).avatar_radius.set((x, y))
        await ctx.send(f"Avatar radius set to {r}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_pos(self, ctx: commands.Context, x: int, y: int):
        """Sets the position of the profile picture."""
        await self.config.guild(ctx.guild).avatar_pos.set((x, y))
        await ctx.send(f"Member profile position set to ({x}, {y}).")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_border(self, ctx: commands.Context, b: int):
        """Sets the profile picture border width."""
        await self.config.guild(ctx.guild).avatar_border.set(b)
        await ctx.send(f"Avatar border set to {b}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def avatar_border_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Sets the profile picture border color using RGB values."""
        color = (red, green, blue)
        await self.config.guild(ctx.guild).avatar_border_color.set(color)
        await ctx.send(f"Avatar border color set to {color}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_count_overlay(self, ctx: commands.Context, overlay: bool):
        """Sets whether or not to overlay the member count on the background."""
        await self.config.guild(ctx.guild).member_count_overlay.set(overlay)
        await ctx.send(f"Member count overlay set to {overlay}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_count_overlay_pos(self, ctx: commands.Context, x: int, y: int):
        """Sets the position of the member count overlay."""
        await self.config.guild(ctx.guild).member_count_overlay_pos.set((x, y))
        await ctx.send(f"Member count overlay position set to ({x}, {y}).")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_joined_overlay(self, ctx: commands.Context, overlay: bool):
        """Sets whether or not to overlay the member joined message on the background."""
        await self.config.guild(ctx.guild).member_joined_overlay.set(overlay)
        await ctx.send(f"Member joined overlay set to {overlay}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_joined_overlay_pos(self, ctx: commands.Context, x: int, y: int):
        """Sets the position of the member joined overlay."""
        await self.config.guild(ctx.guild).member_joined_overlay_pos.set((x, y))
        await ctx.send(f"Member joined overlay position set to ({x}, {y}).")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_join_message(self, ctx: commands.Context, *, message: str):
        """Sets the message to send when a member joins.
        Variables: {member}, {guild}, {guild_owner}, {channel}
        Example: !welcomeset member_join_message {member} joined {guild}! Welcome!
        Variables in {} will be replaced with the appropriate value."""
        await self.config.guild(ctx.guild).member_join_message.set(message)
        await ctx.send(f"Member join message set to {message}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_join_roles(self, ctx: commands.Context, *roles: discord.Role):
        """Sets the roles to give to a member when they join."""
        await self.config.guild(ctx.guild).member_join_roles.set([role.id for role in roles])
        await ctx.send(f"Member join roles set to {[role.name for role in roles]}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def join_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Sets the channel to send the welcome message in."""
        await self.config.guild(ctx.guild).join_channel.set(channel.id)
        await ctx.send(f"Join channel set to {channel.mention}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def member_leave_message(self, ctx: commands.Context, *, message: str):
        """Sets the message to send when a member leaves.
        Variables: {member}
        Example: !welcomeset member_leave_message {member} left! Goodbye!
        Variables in {} will be replaced with the appropriate value."""
        await self.config.guild(ctx.guild).member_leave_message.set(message)
        await ctx.send(f"Member leave message set to {message}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def text_size(self, ctx: commands.Context, size: int):
        """Sets the size of the text."""
        await self.config.guild(ctx.guild).text_size.set(size)
        await ctx.send(f"Text size set to {size}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def count_size(self, ctx: commands.Context, size: int):
        """Sets the size of the count."""
        await self.config.guild(ctx.guild).count_size.set(size)
        await ctx.send(f"Count size set to {size}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def text_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Sets the color of the text using RGB values."""
        color = (red, green, blue)
        await self.config.guild(ctx.guild).text_color.set(color)
        await ctx.send(f"Text color set to {color}.")

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def count_color(self, ctx: commands.Context, red: int, green: int, blue: int):
        """Sets the color of the count using RGB values."""
        color = (red, green, blue)
        await self.config.guild(ctx.guild).count_color.set(color)
        await ctx.send(f"Count color set to {color}.")


    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def test(self, ctx: commands.Context, member: Optional[discord.Member]):
        """Tests the welcome message."""
        if not member:
            member = ctx.author

        async with self.config.guild(member.guild).all() as settings:
            msg = f"{member.name} joined the server!"
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
            w, h = 1100, 500
            background = Image.new(mode="RGBA", size=(w, h), color=(23, 24, 30))
            img = ImageDraw.Draw(background)
            img.rectangle([(75, 25), (w - 75, h - 25)], fill=(0, 0, 0))

        r = settings["avatar_radius"] + settings["avatar_border"]
        img.ellipse((settings["avatar_pos"][0]-r, settings["avatar_pos"][1]-r, settings["avatar_pos"][0]+r, settings["avatar_pos"][1]+r), fill=tuple(settings["avatar_border_color"]))

        r = settings["avatar_radius"]
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

        if settings["member_joined_overlay"]:
            draw = ImageDraw.Draw(background)
            draw.text(settings["member_joined_overlay_pos"], msg, tuple(settings["text_color"]), font=self.get_font(settings["text_size"]), anchor="mm")

        if settings["member_count_overlay"]:
            draw = ImageDraw.Draw(background)
            draw.text(settings["member_count_overlay_pos"], f"Member #{member.guild.member_count}", tuple(settings["count_color"]), font=self.get_font(settings["count_size"]), anchor="mm")
        return background

    def get_font(self, size: int):
        try:
            return ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def reset(self, ctx: commands.Context):
        """Resets all settings to default."""
        await self.config.guild(ctx.guild).clear()
        with suppress(FileNotFoundError):
            os.remove(cog_data_path(self) / f"background-{ctx.guild.id}.png")
        await ctx.send("Settings reset.")
