from .musicrestricter import MusicRestricter


async def setup(bot):
    await bot.add_cog(MusicRestricter(bot))
