import discord
from discord import Interaction, app_commands
from redbot.core import commands
from redbot.core import Config
import asyncio

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()

class ReadyChecker(commands.Cog):
    """Checks which homies are ready tonight"""
    def __init__(self, bot):
        self.bot = bot
            
    @commands.command(description="Check if your homies are ready")
    async def readycheck(self, ctx: commands.Context):
        """Check if your homies are ready"""
        #for mem in ctx.guild.members():
        view = Confirm()
        await ctx.send('Do you want to continue?', view=view)
        # Wait for the View to stop listening for input...
        await view.wait()
        if view.value is None:
            await ctx.send("Timedout")
        elif view.value:
            await ctx.send('Confirmed...')
        else:
            await ctx.send('Cancelled...')


            
            
   