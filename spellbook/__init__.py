from .spellbook import Spellbook


async def setup(bot):
    await bot.add_cog(Spellbook(bot))
