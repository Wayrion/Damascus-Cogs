import discord
from redbot.core import commands
from redbot.core import Config  

class MusicRestricter(commands.Cog):
    """A cog to stop multiple music bots from playing at once"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=718395193090375700, force_registration=True)

        default_guild = {
            "state": True,
            "channels": [],
            "musicbots": []        
        }

        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        state = await self.config.guild(member.guild).state()
        channels = await self.config.guild(member.guild).channels()
        musicbots = await self.config.guild(member.guild).musicbots()
        number_of_bots = 0

        if not state:
            return

        if member.bot == False:
            return

        if before.channel is None and after.channel is not None:
            if after.channel.id not in channels:
                for musicbot in musicbots:
                    for i in after.channel.members:
                        if i.id == musicbot:
                            number_of_bots += 1
        
        if number_of_bots > 1:
            await member.move_to(None)

    @commands.group(name="mrs")
    @commands.is_owner()
    async def musicrestrictersettings(self, ctx):
        """
        Settings for the Music Restricter Cog
        """
        pass

    @musicrestrictersettings.command(name="state")
    @commands.is_owner()
    async def musicrestrictersettings_state(self, ctx, state: bool):
        """
        Toggle the state of the Music Restricter Cog
        """
        await self.config.guild(ctx.guild).state.set(state)
        await ctx.send(f"Cog state set to {state}")


    @musicrestrictersettings.command(name="musicbots")
    @commands.is_owner()
    async def musicrestrictersettings_bots(self, ctx, *, id: int):
        """
        Set the join message for the VC Logger cog
        """
        guild_group = self.config.guild(ctx.guild)

        async with guild_group.musicbots() as musicbots:
            if id in musicbots:
                musicbots.remove(id)
                await ctx.send("Music Bot removed")
            else:
                musicbots.append(id)
                await ctx.send("Music Bot added")

    @musicrestrictersettings.command(name="channels")
    @commands.is_owner()
    async def musicrestrictersettings_channels(self, ctx, *, id: int):
        """
        Set which channels to monitor
        """
        guild_group = self.config.guild(ctx.guild)

        async with guild_group.channels() as channels:
            if id in channels:
                channels.remove(id)
                await ctx.send("Channel removed")
            else:
                channels.append(id)
                await ctx.send("Channel added")

    
    @musicrestrictersettings.command(name="reset")
    @commands.is_owner()
    async def vcloggersettings_reset(self, ctx):
        """
        Reset the VC Logger cog
        """
        await self.config.guild(ctx.guild).clear()
        await ctx.send("VC Logger settings reset")
