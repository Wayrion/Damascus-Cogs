from .cocktail import Cocktail

async def setup(bot):
    await bot.add_cog(Cocktail(bot))