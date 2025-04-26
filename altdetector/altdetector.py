import asyncio
import os
import secrets
from threading import Thread

import discord
from flask import Flask, redirect, request, url_for
from flask_discord import DiscordOAuth2Session, requires_authorization
from redbot.core import Config, commands
from waitress import serve


class AltDetector(commands.Cog):
    """AltDetector cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=718395193090375700)

        default_global = {
            "HOST": "127.0.0.1",
            "PORT": 7144,
            "WAIT_TIME": 60,
            "DISCORD_CLIENT_ID": "[INSERT CLIENT ID HERE]",
            "DISCORD_CLIENT_SECRET": "[INSERT CLIENT SECRET HERE]",
            "DISCORD_REDIRECT_URI": "http://normal-presents.gl.at.ply.gg:7144/callback",
            "DOMAIN": "http://normal-presents.gl.at.ply.gg:7144/",
        }

        default_guild = {
            "enabled": True,
            "log_channel": None,
            "registered_users": [],
            "registered_ips": [],
            "banned_ips": [],
            "whitelist": [],
            "member_join_roles": [],
            "action": "ban",
            "reason": "Alt account detected.",
        }

        self.app = Flask("AltDetector")
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        self.app.config["SECRET_KEY"] = secrets.token_hex(24)
        self.app.config["DISCORD_CLIENT_ID"] = default_global["DISCORD_CLIENT_ID"]
        self.app.config["DISCORD_CLIENT_SECRET"] = default_global[
            "DISCORD_CLIENT_SECRET"
        ]
        self.app.config["DISCORD_REDIRECT_URI"] = default_global["DISCORD_REDIRECT_URI"]
        self.discord_auth = DiscordOAuth2Session(self.app)
        self.user_data = None

        @self.app.route("/")
        def home():
            page = open(
                os.path.dirname(os.path.realpath(__file__)) + "/data/home.html", "r"
            )
            return page

        @self.app.route("/login")
        def login():
            self.user_data = None
            return self.discord_auth.create_session()

        @self.app.route("/callback")
        def callback():
            self.discord_auth.callback()
            return redirect(url_for("dashboard"))

        @self.app.route("/dashboard")
        @requires_authorization
        def dashboard():
            user_ip = request.remote_addr
            user = self.discord_auth.fetch_user()
            avatar_url = user.avatar_url
            user_ip = request.remote_addr
            self.user_data = {
                "name": user.username,
                "id": user.id,
                "ip": user_ip,
                "banned": False,
                "ban_reason": None,
            }

            with open(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "data", "dashboard.txt"
                ),
                "r",
            ) as file:
                content = file.read()

            return content.format(user=user, avatar_url=avatar_url)

        Thread(
            target=serve,
            args=(self.app,),
            kwargs={"host": default_global["HOST"], "port": default_global["PORT"]},
        ).start()

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        whitelist = await self.config.guild(member.guild).whitelist()
        log_channel = await self.config.guild(member.guild).log_channel()

        if not await self.config.guild(member.guild).enabled():
            return

        if member.bot or member.id in whitelist:
            return

        registered_users = await self.config.guild(member.guild).registered_users()
        domain = await self.config.DOMAIN()
        wait_time = await self.config.WAIT_TIME()
        wait_time = 60

        embed = discord.Embed(
            title="Verification Process",
            description=f"Please login to the given website to complete the verification process. This may take up to {wait_time} seconds to complete.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Website:", value=f"{domain}", inline=True)
        await member.send(embed=embed)

        await asyncio.sleep(wait_time)

        if member not in member.guild.members:
            return

        if self.user_data is None:
            embed = discord.Embed(
                title="Verification Process",
                description="You didn't login in time, please try again.",
                color=discord.Color.red(),
            )
            await member.kick(reason="Didn't login in time")

            if log_channel is not None:
                channel = member.guild.get_channel(log_channel)
                embed = discord.Embed(
                    title="Verification Process",
                    description=f"{member.mention} didn't login in time and was kicked.",
                    color=discord.Color.red(),
                )
                await channel.send(embed=embed)
            return

        if (
            self.user_data["ip"]
            in str(
                open(
                    os.path.dirname(os.path.realpath(__file__)) + "/data/ipv4.txt", "r"
                )
            ).splitlines()
        ):

            embed = discord.Embed(
                title="Verification Process",
                description="You are using a VPN, please disable it and try again.",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
            await member.kick(reason="Using VPN")

            if log_channel is not None:
                channel = member.guild.get_channel(log_channel)
                embed = discord.Embed(
                    title="Verification Process",
                    description=f"{member.mention} is using a VPN and was kicked.",
                    color=discord.Color.red(),
                )
                await channel.send(embed=embed)
            return

        async with self.config.guild(member.guild).banned_ips() as banned_ips:
            if self.user_data["ip"] in banned_ips:

                embed = discord.Embed(
                    title="Verification Process",
                    description="You are using a banned IP, please contact the server staff.",
                    color=discord.Color.red(),
                )

                await member.send(embed=embed)
                await member.ban(reason="Banned IP")

                if log_channel is not None:
                    channel = member.guild.get_channel(log_channel)

                    embed = discord.Embed(
                        title="Verification Process",
                        description=f"{member.mention} has a banned IP and was banned.",
                        color=discord.Color.red(),
                    )

                    await channel.send(embed=embed)
                return

        for user in registered_users:
            # Act on the alt account
            if user["ip"] == self.user_data["ip"] and user["id"] != member.id:
                action = await self.config.guild(member.guild).action()
                if action != "none":
                    act = getattr(member, action)
                    reason = await self.config.guild(member.guild).reason()
                    await act(reason=reason)
                    embed = discord.Embed(
                        title="Verification Process",
                        description=f"{member.mention} is an alt account and was {action}ed.",
                        color=discord.Color.red(),
                    )

                    if log_channel is not None:
                        channel = member.guild.get_channel(log_channel)
                        await channel.send(embed=embed)

        async with self.config.guild(
            member.guild
        ).registered_users() as registered_users:
            registered_users.append(self.user_data)
            print(registered_users)

        async with self.config.guild(
            member.guild
        ).member_join_roles() as member_join_roles:
            try:
                for role in member_join_roles:
                    await member.add_roles(member.guild.get_role(role))

                embed = discord.Embed(
                    title="Verification Process",
                    description=f"{member.mention} has been given the roles {', '.join([member.guild.get_role(role).mention for role in member_join_roles])}.",
                    color=discord.Color.green(),
                )

                if log_channel is not None:
                    channel = member.guild.get_channel(log_channel)
                    await channel.send(embed=embed)

            except asyncio.TimeoutError:
                pass

            except (
                discord.Forbidden
            ):  # If the bot doesn't have permissions to add roles / role is the same or higher than the bot's top role
                pass

        await member.send("You have been verified, welcome to the server!")

        if log_channel is not None:
            channel = member.guild.get_channel(log_channel)
            embed = discord.Embed(
                title="Verification Process",
                description=f"{member.mention} has been verified.",
                color=discord.Color.green(),
            )
            await channel.send(embed=embed)

        self.user_data = None

    @commands.Cog.listener()
    async def on_member_ban(self, member: discord.Member):
        log_channel = await self.config.guild(member.guild).log_channel()

        async with self.config.guild(
            member.guild
        ).registered_users() as registered_users:
            for user in registered_users:
                if user["id"] == member.id:
                    async with self.config.guild(
                        member.guild
                    ).banned_ips() as banned_ips:
                        try:
                            banned_ips.append(user["ip"])

                            if log_channel is not None:
                                channel = member.guild.get_channel(log_channel)
                                embed = discord.Embed(
                                    title="Verification Process",
                                    description=f"{member.mention}'s IP has been added to the banned IPs list.",
                                    color=discord.Color.red(),
                                )
                                await channel.send(embed=embed)

                        except:
                            pass
                    break

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        log_channel = await self.config.guild(guild).log_channel()

        async with self.config.guild(guild).banned_ips() as banned_ips:
            try:
                banned_ips.remove(user["ip"])

                if log_channel is not None:
                    channel = guild.get_channel(log_channel)
                    embed = discord.Embed(
                        title="Verification Process",
                        description=f"{user.mention}'s IP has been removed from the banned IPs list.",
                        color=discord.Color.green(),
                    )
                    await channel.send(embed=embed)

            except:
                pass

    @commands.command()
    @commands.is_owner()
    async def nukeconfig(self, ctx):
        """Nuke the config"""
        await self.config.clear_all()
        await ctx.send("Nuked the config")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx):
        """Enable the cog"""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Enabled the cog")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        """Disable the cog"""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Disabled the cog")

    @commands.command()
    @commands.is_owner()
    async def sethost(self, ctx, host: str):
        """Set the host"""
        await self.config.HOST.set(host)
        await ctx.send(f"Set host to {host}")

    @commands.command()
    @commands.is_owner()
    async def setclientid(self, ctx, DISCORD_CLIENT_ID: str):
        """Set the DISCORD_CLIENT_ID"""
        await self.config.DISCORD_CLIENT_ID.set(DISCORD_CLIENT_ID)
        await ctx.send(f"Set DISCORD_CLIENT_ID to {DISCORD_CLIENT_ID}")

    @commands.command()
    @commands.is_owner()
    async def setclientsecret(self, ctx, DISCORD_CLIENT_SECRET: str):
        """Set the DISCORD_CLIENT_SECRET"""
        await self.config.DISCORD_CLIENT_SECRET.set(DISCORD_CLIENT_SECRET)
        await ctx.send(f"Set DISCORD_CLIENT_SECRET to {DISCORD_CLIENT_SECRET}")

    @commands.command()
    @commands.is_owner()
    async def setdomain(self, ctx, domain: str):
        """Set the domain"""
        await self.config.DOMAIN.set(domain)
        await self.config.DISCORD_REDIRECT_URI.set(f"{domain}/callback")
        await ctx.send(f"Set domain to {domain}")

    @commands.command()
    @commands.is_owner()
    async def setwaittime(self, ctx, wait_time: int):
        """Set the wait time"""
        await self.config.WAIT_TIME.set(wait_time)
        await ctx.send(f"Set wait time to {wait_time}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Set the log channel"""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Set the log channel to {channel.mention}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setaction(self, ctx, action: str):
        """Set the action to take when an alt account is detected"""

        if action.lower() not in ["ban", "kick", "none"]:
            await ctx.send("The action must be either ban or kick or none")
            return

        await self.config.guild(ctx.guild).action.set(action)
        await ctx.send(f"Set the action to {action}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setreason(self, ctx, *, reason: str):
        """Set the reason for the action"""
        await self.config.guild(ctx.guild).reason.set(reason)
        await ctx.send(f"Set the reason to {reason}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addbannedip(self, ctx, ip: str):
        """Add an IP to the banned IPs list"""
        async with self.config.guild(ctx.guild).banned_ips() as banned_ips:
            banned_ips.append(ip)
            await ctx.send(f"Added `{ip}` from the banned IPs list")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def removebannedip(self, ctx, ip: str):
        """Remove an IP from the banned IPs list"""
        async with self.config.guild(ctx.guild).banned_ips() as banned_ips:
            try:
                banned_ips.remove(ip)
                await ctx.send(f"Removed `{ip}` from the banned IPs list")
            except:
                await ctx.send(f"`{ip}` is not in the banned IPs list")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def showbannedips(self, ctx):
        """Show the banned IPs list"""
        banned_ips = await self.config.guild(ctx.guild).banned_ips()
        await ctx.send(f"Banned IPs: {banned_ips}")

    @commands.command(name="join_roles")
    @commands.admin_or_permissions(manage_guild=True)
    async def member_join_roles(self, ctx: commands.Context, *roles: discord.Role):
        """Set the roles to give to a member when they join."""
        await self.config.guild(ctx.guild).member_join_roles.set(
            [role.id for role in roles]
        )
        await ctx.send(f"Member join roles set to {[role.name for role in roles]}.")
