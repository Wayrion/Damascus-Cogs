from .readychecker import ReadyChecker


async def setup(bot):
    await bot.add_cog(ReadyChecker(bot))
