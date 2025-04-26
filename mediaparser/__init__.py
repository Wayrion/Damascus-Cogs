from .mediaparser import MediaParser


async def setup(bot):
    await bot.add_cog(MediaParser(bot))
