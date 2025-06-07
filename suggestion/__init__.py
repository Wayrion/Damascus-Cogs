from .suggestion import Suggestion
from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(Suggestion(bot))
