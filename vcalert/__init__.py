from .vcalert import VCAlert


async def setup(bot):
    await bot.add_cog(VCAlert(bot))
