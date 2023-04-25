import discord
from redbot.core import commands
import random
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

class DiceRoller(commands.Cog):
    """A cog for a fudge rolling dice"""
    
    def __init__(self, bot):
        self.bot = bot

    def chunks(self, lst):
        chunks = []
        for i in pagify(str(lst), delims=[','], page_length=300):
            i = str(i)
            result = str("```" + i + "```")
            result = result.replace("'", "")
            result = result.replace("[", "")
            result = result.replace("]", "")
            print(result)
            chunks.append(result)

        return chunks

    def convert_modifier(self, modifier):
        whitelistedchars = ['+', '-', '*', "/", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        if modifier == "":
            return 0

        else:
            try:
                modifier = modifier.lower()
                for i in modifier:
                    if i not in whitelistedchars:
                        modifier.replace(i, "")
                
                try:
                    modifier = int(eval(modifier))
                    return modifier
                except:
                    return 0
            except:
                return 0
                

    @commands.command()
    async def fudge(self, ctx, argument, *, reason: str = None):
        """Roll a Fudge dice"""

        options = ["➕", "🔲", "➖"]
        results = []


        values = {
            "➕": 1,
            "🔲": 0,
            "➖": -1
        }

        parsed_argument = argument.lower().split("df")
        try:
            number = abs(int(parsed_argument[0]))
            modifier = self.convert_modifier(parsed_argument[1])

            if number <= 50000:
                for i in range(number):
                    results.append(random.choice(options))

                total = sum(values[i] for i in results) + modifier
                await ctx.send(f"{ctx.message.author.mention} rolled {reason}, with the argument `{argument}` and got a total of `{total}`")
                if len(results) > 50:
                    await menu(ctx=ctx, pages=self.chunks(results), controls=DEFAULT_CONTROLS)
                else:
                    await ctx.send(f"```{results}```")

            else:
                await ctx.send("The number of dices must be less than 50,000")

        except:
            await ctx.send(f"Invalid input. Please follow the format: `{list(await self.bot.get_prefix(ctx.message))[0]}fudge <number>df<modifier> [reason]`")


    
    @commands.command()
    async def roll(self, ctx, argument, *, reason: str = None):
        """Roll a normal dice"""

        results = []
        
        parsed_argument = argument.lower().split("df")
        
        try:
            number = abs(int(parsed_argument[0]))
            faces = abs(int(parsed_argument[1]))

            if number <= 50000 and faces <= 50000:
                for i in range(number):
                    results.append(random.choice(range(1, faces)))

                total = sum(int(i) for i in results)
                await ctx.send(f"{ctx.message.author.mention} rolled {reason}, with the argument `{argument}` and got a total of `{total}`")
                if len(results) > 50:
                    await menu(ctx=ctx, pages=self.chunks(results), controls=DEFAULT_CONTROLS)
                else:
                    await ctx.send(f"```{results}```")
            
            else:
                await ctx.send("The number of dices and faces must be less than 50,000")

        except:
            await ctx.send(f"Invalid input. Please follow the format: `{list(await self.bot.get_prefix(ctx.message))[0]}roll <number>df<modifier>` [reason]")
