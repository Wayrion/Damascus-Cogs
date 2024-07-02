import discord
from redbot.core import commands
from redbot.core import Config, checks


class Automuter(commands.Cog):
    """Automuter cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=718395193090375700, force_registration=True
        )

        default_guild = {
            "state": True,
            "unmute": True,
            "undeafen": True,
            "disconnect": False,
        }

        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):

        state = await self.config.guild(member.guild).state()
        unmute = await self.config.guild(member.guild).unmute()
        undeafen = await self.config.guild(member.guild).undeafen()
        disconnect = await self.config.guild(member.guild).disconnect()

        if not state:
            return

        if before.channel is None and after.channel is not None:
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
    async def automuter(self, ctx):
        """
        Settings for the Automuter cog
        """
        pass

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def state(self, ctx, state: bool):
        """
        Toggle the state of the Automuter cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send(f"Automuter state set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def unmute(self, ctx, state: bool):
        """
        Toggle the state of the unmute
        """
        await self.config.guild(ctx.guild).unmute.set(state)
        await ctx.send(f"Automuter unmute set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def undeafen(self, ctx, state: bool):
        """
        Toggle the state of the undeafen
        """
        await self.config.guild(ctx.guild).undeafen.set(state)
        await ctx.send(f"Automuter undeafen set to {state}")

    @automuter.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def disconnect(self, ctx, state: bool):
        """
        Toggle the state of the disconnect
        """
        await self.config.guild(ctx.guild).disconnect.set(state)
        await ctx.send(f"Automuter disconnect set to {state}")

    @automuter.command()
    @checks.admin()
    async def reset(self, ctx: commands.Context):
        """Reset all settings to the default values."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Settings reset.")
