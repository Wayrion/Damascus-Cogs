from .automuter import Automuter


async def setup(bot):
    await bot.add_cog(Automuter(bot))
