import random

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu


class VCLogger(commands.Cog):
    """A VCLogger cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=718395193090375700, force_registration=True
        )

        default_guild = {
            "state": True,
            "empty_only": True,
            "logchannel": None,
            "join_msg": ["{member.mention} joined the vc"],
            "leave_msg": ["{member.mention} left the vc"],
        }

        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        join_msg = random.choice(await self.config.guild(member.guild).join_msg())
        leave_msg = random.choice(await self.config.guild(member.guild).leave_msg())
        logchannel = await self.config.guild(member.guild).logchannel()
        state = await self.config.guild(member.guild).state()
        empty_only = await self.config.guild(member.guild).empty_only()

        if not state:
            return

        if logchannel is None:
            return

        if before.channel is None and after.channel is not None:
            try:
                channel = self.bot.get_channel(logchannel)

                if empty_only == False:
                    if "{member.mention}" in join_msg:
                        await channel.send(join_msg.format(member=member))
                    elif join_msg != "":
                        await channel.send(join_msg)

                elif (empty_only == True) and len(after.channel.members) == 1:
                    if "{member.mention}" in join_msg:
                        await channel.send(join_msg.format(member=member))
                    elif join_msg != "":
                        await channel.send(join_msg)

                else:
                    return

            except:
                return

        elif before.channel is not None and after.channel is None:
            try:
                channel = self.bot.get_channel(logchannel)
                if empty_only == False:
                    if "{member.mention}" in leave_msg:
                        await channel.send(leave_msg.format(member=member))

                    elif leave_msg != "":
                        await channel.send(leave_msg)

                    else:
                        return

                elif (empty_only == True) and len(before.channel.members) == 0:
                    if "{member.mention}" in leave_msg:
                        await channel.send(leave_msg.format(member=member))

                    elif leave_msg != "":
                        await channel.send(leave_msg)

                    else:
                        return

            except:
                return

    @commands.group(name="vcls")
    @commands.is_owner()
    async def vcloggersettings(self, ctx: commands.Context):
        """
        Settings for the VC Logger cog
        """
        pass

    @vcloggersettings.command(name="state")
    @commands.is_owner()
    async def vcloggersettings_state(self, ctx, state: bool):
        """
        Toggle the state of the VC Logger cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send(f"VC Logger state set to {state}")

    @vcloggersettings.command(name="emptyonly")
    @commands.is_owner()
    async def vcloggersettings_emptyonly(self, ctx, state: bool):
        """
        Toggle the emptyonly setting of the VC Logger cog
        """
        await self.config.guild(ctx.guild).empty_only.set(state)
        await ctx.send(f"VC Logger emptyonly setting set to {state}")

    @vcloggersettings.command(name="logchannel")
    @commands.is_owner()
    async def vcloggersettings_logchannel(self, ctx, channel: int):
        """
        Set the log channel for the VC Logger cog
        """
        await self.config.guild(ctx.guild).logchannel.set(channel)
        await ctx.send(f"VC Logger log channel set to <#{channel}>")

    @vcloggersettings.command(name="joinmsg")
    @commands.is_owner()
    async def vcloggersettings_joinmsg(self, ctx, *, response: str = None):
        """
        Set the join message for the VC Logger cog
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.join_msg() as responses:
            if response in responses:
                responses.remove(response)
                await ctx.send("Join message removed")
            else:
                responses.append(response)
                await ctx.send("Join message added")

    @vcloggersettings.command(name="leavemsg")
    @commands.is_owner()
    async def vcloggersettings_leavemsg(self, ctx, *, response: str = None):
        """
        Set the leave message for the VC Logger cog
        """
        guild_group = self.config.guild(ctx.guild)
        async with guild_group.leave_msg() as responses:
            if response in responses:
                responses.remove(response)
                await ctx.send("Leave message removed")
            else:
                responses.append(response)
                await ctx.send("Leave message added")

    @vcloggersettings.command(name="listjoinmsg")
    @commands.is_owner()
    async def vcloggersettings_listjoinmsg(self, ctx: commands.Context):
        """
        Lists the joins msgs for the vc logger cog with
        """

        guild_group = self.config.guild(ctx.guild)
        join_msg = await guild_group.join_msg()
        x = [join_msg[i : i + 10] for i in range(0, len(join_msg), 10)]
        pages = []
        for a in x:
            embed = discord.Embed(
                title="Join Messages", description=a, color=discord.Color.random()
            )
            pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS)

    @vcloggersettings.command(name="listleavemsg")
    @commands.is_owner()
    async def vcloggersettings_listleavemsg(self, ctx: commands.Context):
        """
        Lists the leave msgs for the vc logger cog with
        """

        guild_group = self.config.guild(ctx.guild)
        leave_msg = await guild_group.leave_msg()
        x = [leave_msg[i : i + 10] for i in range(0, len(leave_msg), 10)]
        pages = []
        for a in x:
            embed = discord.Embed(
                title="Leave Messages", description=a, color=discord.Color.random()
            )
            pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS)

    @vcloggersettings.command(name="reset")
    @commands.is_owner()
    async def vcloggersettings_reset(self, ctx: commands.Context):
        """
        Reset the VC Logger cog
        """
        await self.config.guild(ctx.guild).clear()
        await ctx.send("VC Logger settings reset")

    @vcloggersettings.command(name="show")
    @commands.is_owner()
    async def vcloggersettings_show(self, ctx: commands.Context):
        """
        Shows current configurations for the cog
        """

        logchannel = await self.config.guild(ctx.guild).logchannel()
        state = await self.config.guild(ctx.guild).state()
        empty_only = await self.config.guild(ctx.guild).empty_only()

        embed = discord.Embed(
            title="VCLogger cog settings", color=discord.Color.random()
        )
        embed.add_field(name="State:", value=state, inline=True)
        embed.add_field(name="Empty Only:", value=empty_only, inline=True)
        embed.add_field(name="Log Channel:", value=f"<#{logchannel}>", inline=True)

        await ctx.send(embed=embed)
