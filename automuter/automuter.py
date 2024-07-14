import discord
from redbot.core import commands
from redbot.core import Config, checks
import asyncio
from redbot.core.utils.chat_formatting import humanize_list


class Automuter(commands.Cog):
    """Automuter cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=718395193090375700, force_registration=True
        )

        default_channel = {
            "state": False,
            "unmute": True,
            "undeafen": True,
            "disconnect": False,
            "time": 5,
        }

        self.config.register_channel(**default_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if after.channel == None:
            return

        if before.channel != after.channel:
            # This is some janky code
            vc = after.channel
            time = int(await self.config.channel(vc).time())
            state = await self.config.channel(vc).state()

            if not state:
                return
            await asyncio.sleep(time)

            state = await self.config.channel(vc).state()

            if not state:
                return

            if member.voice.channel != vc:
                return

            unmute = await self.config.channel(vc).unmute()
            undeafen = await self.config.channel(vc).undeafen()
            disconnect = await self.config.channel(vc).disconnect()

            try:
                if unmute:
                    await member.edit(mute=False)
                if undeafen:
                    await member.edit(deafen=False)
            except:
                return

            if disconnect:
                await member.edit(voice_channel=None)

    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def automuter(self, ctx: commands.Context):
        """
        Settings for the Automuter cog
        """
        pass

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def state(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the Automuter cog
        """
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return
        await self.config.channel(ctx.channel).state.set(state)
        await ctx.send(f"Automuter state set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def unmute(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the unmute
        """
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return

        await self.config.channel(ctx.channel).unmute.set(state)
        await ctx.send(f"Automuter unmute set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def undeafen(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the undeafen
        """
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return
        await self.config.channel(ctx.channel).undeafen.set(state)
        await ctx.send(f"Automuter undeafen set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def disconnect(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the disconnect
        """
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return
        await self.config.channel(ctx.channel).disconnect.set(state)
        await ctx.send(f"Automuter disconnect set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def time(self, ctx: commands.Context, time: int):
        """
        Toggle the amount of time before an action"""
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return
        await self.config.channel(ctx.channel).time.set(time)
        await ctx.send(f"Automuter waiting time set to {time}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def list(self, ctx: commands.Context):
        """
        List all the channels that have automuter enabled
        """
        enabled_channels = []
        for i in ctx.guild.channels:
            state = await self.config.channel(i).state()

            if state:
                enabled_channels.append(f"<#{i.id}>\n")

        await ctx.send(humanize_list(enabled_channels))

    @automuter.command()
    @checks.admin()
    async def reset(self, ctx: commands.Context):
        """Reset channel settings to the default values."""
        if str(ctx.channel.type) != "voice":
            await ctx.send("You are not in a voice channel")
            return
        await self.config.channel(ctx.channel).clear()
        await ctx.send("Settings reset.")

    @automuter.command()
    @checks.admin()
    async def nukeconfig(self, ctx: commands.Context):
        """
        This command nukes the config
        """
        await self.config.clear_all()
        await ctx.send("Config cleared")
