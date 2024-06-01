from .notifier import Notifier


async def setup(bot):
    await bot.add_cog(Notifier(bot))
