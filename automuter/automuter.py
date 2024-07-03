import discord
from redbot.core import commands
from redbot.core import Config, checks
import asyncio


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
        }

        self.config.register_channel(**default_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):

        vc: discord.VoiceChannel = after.channel

        state = await self.config.channel(vc).state()
        unmute = await self.config.channel(vc).unmute()
        undeafen = await self.config.channel(vc).undeafen()
        disconnect = await self.config.channel(vc).disconnect()

        if not state:
            return

        await asyncio.sleep(5)

        if after.channel is not None:
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
        await self.config.channel(ctx.channel).state.set(state)
        await ctx.send(f"Automuter state set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def unmute(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the unmute
        """
        await self.config.channel(ctx.channel).unmute.set(state)
        await ctx.send(f"Automuter unmute set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def undeafen(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the undeafen
        """
        await self.config.channel(ctx.channel).undeafen.set(state)
        await ctx.send(f"Automuter undeafen set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def disconnect(self, ctx: commands.Context, state: bool):
        """
        Toggle the state of the disconnect
        """
        await self.config.channel(ctx.channel).disconnect.set(state)
        await ctx.send(f"Automuter disconnect set to {state}")

    @automuter.command()
    @checks.admin()
    async def reset(self, ctx: commands.Context):
        """Reset all settings to the default values."""
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
