import discord
import asyncio
import time
import os
from redbot.core import Config, commands, checks
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

class Welcome(commands.Cog):
    """Welcomes a user to the server with an image."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 718395193090375700, force_registration=True)
        default_guild  = {
            "background": False,
            "member_count_overlay": True,
            "member_joined_overlay": True,
            "member_profile_pos": (550, 170),
            "member_joined_overlay_pos": (550,345),
            "member_count_overlay_pos": (550, 413),
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
            path = bundled_data_path(self) / "background.png"
            # Use PIL and overlay the background on the profile picture of the user on coords (550, 170)
            file = open(bundled_data_path(self) / "arial.ttf", "rb")
            bytes_font = BytesIO(file.read())
            font=ImageFont.truetype(bytes_font, 35)
            background = Image.open(path)
            profile = Image.open(BytesIO(await member.avatar.read()))
            profile = profile.resize((300, 300))
            profile_size = profile.size

            # Create a new image with a white background
            circle_image = Image.new("RGBA", (300, 300), (255, 255, 255, 0))

            # Draw a circle on the new image
            draw = ImageDraw.Draw(circle_image)
            draw.ellipse((0, 0, 300, 300), fill=(255, 255, 255, 255))

            # Use the circle image as a mask for the profile image
            profile = Image.composite(profile, circle_image, circle_image)

            # Paste the profile image onto the background at the specified position
            val = (settings["member_profile_pos"][0] - profile_size[0] // 2, settings["member_profile_pos"][1] - profile_size[1] // 2)
            background.paste(profile, val, profile)

            if settings["member_joined_overlay"]:
                draw = ImageDraw.Draw(background)
                draw.text(settings["member_joined_overlay_pos"], f"{member.name}#{member.discriminator} joined the server!", (0, 0, 0), font=font, anchor="mm")

            if settings["member_count_overlay"]:
                draw = ImageDraw.Draw(background)
                draw.text(settings["member_count_overlay_pos"], f"Member #{member.guild.member_count}", (0, 0, 0), font=font, anchor="mm")

            background.save(bundled_data_path(self) / f"welcome{member.id}.png")
        

            if settings["join_channel"]:
                channel = member.guild.get_channel(settings["join_channel"])
                await channel.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=channel), file=discord.File(bundled_data_path(self) / f"welcome{member.id}.png"))

            else:
                await member.guild.system_channel.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name), file=discord.File(bundled_data_path(self) / f"welcome{member.id}.png"))
    
            
            os.remove(bundled_data_path(self) / f"welcome{member.id}.png")

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
            path = bundled_data_path(self) / "background.png"
            # Use PIL and overlay the background on the profile picture of the user on coords (550, 170)
            file = open(bundled_data_path(self) / "arial.ttf", "rb")
            bytes_font = BytesIO(file.read())
            font=ImageFont.truetype(bytes_font, 35)
            background = Image.open(path)
            profile = Image.open(BytesIO(await member.avatar.read()))
            profile = profile.resize((300, 300))
            profile_size = profile.size

            # Create a new image with a white background
            circle_image = Image.new("RGBA", (300, 300), (255, 255, 255, 0))

            # Draw a circle on the new image
            draw = ImageDraw.Draw(circle_image)
            draw.ellipse((0, 0, 300, 300), fill=(255, 255, 255, 255))

            # Use the circle image as a mask for the profile image
            profile = Image.composite(profile, circle_image, circle_image)

            # Paste the profile image onto the background at the specified position
            val = (settings["member_profile_pos"][0] - profile_size[0] // 2, settings["member_profile_pos"][1] - profile_size[1] // 2)
            background.paste(profile, val, profile)

            if settings["member_joined_overlay"]:
                draw = ImageDraw.Draw(background)
                draw.text(settings["member_joined_overlay_pos"], f"{member.name}#{member.discriminator} left the server.", (0, 0, 0), font=font, anchor="mm")

            if settings["member_count_overlay"]:
                draw = ImageDraw.Draw(background)
                draw.text(settings["member_count_overlay_pos"], f"Member #{member.guild.member_count}", (0, 0, 0), font=font, anchor="mm")

            background.save(bundled_data_path(self) / f"goodbye{member.id}.png")

            if settings["join_channel"]:
                channel = member.guild.get_channel(settings["join_channel"])
                await channel.send(settings["member_leave_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=channel), file=discord.File(bundled_data_path(self) / f"goodbye{member.id}.png"))

            else:
                await member.guild.system_channel.send(settings["member_leave_message"].format(member=member.mention, guild=member.guild.name), file=discord.File(bundled_data_path(self) / f"goodbye{member.id}.png"))
            
            os.remove(bundled_data_path(self) / f"goodbye{member.id}.png")
    
    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def welcomeset(self, ctx: commands.Context):
        """Settings for the welcomer cog"""
        pass

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def background(self, ctx: commands.Context):
        """Sets the background image for the welcome message."""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image file to set as the background.")
            return

        # Get the attached file
        file = ctx.message.attachments[0]

        # Check if the attached file is an image
        if not file.filename.endswith((".png", ".jpg", ".jpeg")):
            await ctx.send("Please attach a PNG or JPEG image file.")
            return

        # Save the file to the data folder
        path = bundled_data_path(self) / "background.png"
        await file.save(path)

        # Set the background to True
        await self.config.guild(ctx.guild).background.set(True)

        # Send a message saying that the background was set
        await ctx.send(f"Background set to {file.filename}.")

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
    async def member_profile_pos(self, ctx: commands.Context, x: int, y: int):
        """Sets the position of the member profile picture."""
        await self.config.guild(ctx.guild).member_profile_pos.set((x, y))
        await ctx.send(f"Member profile position set to ({x}, {y}).")

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
    async def test(self, ctx: commands.Context):
        member=ctx.author
        """Tests the welcome message."""
        async with self.config.guild(member.guild).all() as settings:
            path = bundled_data_path(self) / "background.png"
            # Use PIL and overlay the background on the profile picture of the user on coords (550, 170)
            background = Image.open(path)
            profile = Image.open(BytesIO(await member.avatar.read()))
            profile = profile.resize((300, 300))
            profile_size = profile.size

            # Create a new image with a white background
            circle_image = Image.new("RGBA", (300, 300), (255, 255, 255, 0))

            # Draw a circle on the new image
            draw = ImageDraw.Draw(circle_image)
            draw.ellipse((0, 0, 300, 300), fill=(255, 255, 255, 255))

            # Use the circle image as a mask for the profile image
            profile = Image.composite(profile, circle_image, circle_image)

            # Paste the profile image onto the background at the specified position
            val = (settings["member_profile_pos"][0] - profile_size[0] // 2, settings["member_profile_pos"][1] - profile_size[1] // 2)
            background.paste(profile, val, profile)

            if settings["member_joined_overlay"]:
                draw = ImageDraw.Draw(background)
                font = ImageFont.truetype("arial.ttf", 35)
                draw.text(settings["member_joined_overlay_pos"], f"{member.name}#{member.discriminator} joined the server!", (0, 0, 0), font=font, anchor="mm")

            if settings["member_count_overlay"]:
                draw = ImageDraw.Draw(background)
                font = ImageFont.truetype("arial.ttf", 35)
                draw.text(settings["member_count_overlay_pos"], f"Member #{member.guild.member_count}", (0, 0, 0), font=font, anchor="mm")

            background.save(bundled_data_path(self) / f"welcome{member.id}.png")
        

            await ctx.send(settings["member_join_message"].format(member=member.mention, guild=member.guild.name, guild_owner=member.guild.owner, channel=ctx.channel), file=discord.File(bundled_data_path(self) / f"welcome{member.id}.png"))

           
            os.remove(bundled_data_path(self) / f"welcome{member.id}.png")
        

    @welcomeset.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def reset(self, ctx: commands.Context):
        """Resets all settings to default."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Settings reset.")

