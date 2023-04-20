from .vclogger import VCLogger

async def setup(bot):
    await bot.add_cog(VCLogger(bot))