from .diceroller import DiceRoller

async def setup(bot):
    await bot.add_cog(DiceRoller(bot))