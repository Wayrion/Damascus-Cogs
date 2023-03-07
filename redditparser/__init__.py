from .redditparser import Redditparser

async def setup(bot):
    await bot.add_cog(Redditparser(bot))