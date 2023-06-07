from .bible import Bible

async def setup(bot):
    await bot.add_cog(Bible(bot))