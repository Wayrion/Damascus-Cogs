import discord
from redbot.core import commands
#from redbot.core import Config
import aiohttp

from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from .utils import drinksformatter, ingredientformatter, multipledrinksformatter, chunks

class Cocktail(commands.Cog):
    """A cog the Cocktail DB"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group()
    async def cocktail(self, ctx: commands.Context):
        """Cocktail commands"""
        pass
   
    @cocktail.command()
    async def random(self, ctx: commands.Context):
        """Get a random cocktail"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/random.php') as resp:
            
                response = await resp.json()
                
                data=response.get("drinks")
                embed = drinksformatter(data)
                await ctx.send(embed=embed)
        

    #SEARCH COMMANDS
    @cocktail.group()
    async def search(self, ctx: commands.Context):
        """Search commands for Cocktail DB"""
        pass

    @search.command()
    async def name(self, ctx, *, query):
        """Search cocktail by its name"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/search.php?s={query}') as resp:
                
                response = await resp.json()
                data=response.get("drinks")
                if data != None:
                    embed = drinksformatter(data)
                    await ctx.send(embed=embed)

                else:
                    await ctx.send("No results found")
                
    @search.command()
    async def firstletter(self, ctx, *, query):
        """Search cocktail by its first letter"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/search.php?f={query}') as resp:
                
                response = await resp.json()
                data=response.get("drinks")
                embed=discord.Embed(title=f"List of all cocktails starting with {query}",color=discord.Color.random())
                Pages=[]
                
                Cocktails=[]
                if data != None:
                    for i in data:
                        a=i.get("strDrink")
                        Cocktails.append(a)
                        Pages.append(multipledrinksformatter(i, list(data).index(i)))

                    embed.add_field(name=f"Name:", value=f"Page Number", inline=False)
                    for i in Cocktails:
                        embed.add_field(name=f"Results:", value=f"{i} : {Cocktails.index(i)}", inline=False)

                    Pages.insert(0, embed)
                    
                    await menu(ctx, Pages, DEFAULT_CONTROLS)
                else:
                    await ctx.send("No results found")
                                   

    @search.command()
    async def ingredientname(self, ctx, * ,name):
        """Search cocktail by its ingredient"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/search.php?i={name}') as resp:
                
                response = await resp.json()
                data=response.get("ingredients")
                if data != None:
                    embed = ingredientformatter(data)
                    await menu(ctx, embed, DEFAULT_CONTROLS)
                    
                else:
                    await ctx.send("No results found")                

    #LOOKUP COMMANDS
    @cocktail.group()
    async def lookup(self, ctx: commands.Context):
        """Lookup cocktails for Cocktail DB"""
        pass

    @lookup.command()
    async def cocktailid(self, ctx, id):
        """Lookup cocktail by its id"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/lookup.php?i={id}') as resp:
                
                response = await resp.json()
                data=response.get("drinks")
                if data != None:
                    embed = drinksformatter(data)
                    await ctx.send(embed=embed)

                else:
                    await ctx.send("No results found")
    
    @lookup.command()
    async def ingredientid(self, ctx, name):
        """Lookup cocktail by its ingredient"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/lookup.php?iid={name}') as resp:
                
                response = await resp.json()
                data=response.get("ingredients")
                
                if data != None:
                    embed = ingredientformatter(data)
                    await menu(ctx, embed, DEFAULT_CONTROLS)

                else:
                    await ctx.send("No results found")

    #FILTER COMMANDS
    @cocktail.group()
    async def filter(self, ctx: commands.Context):
        """Filter commands for Cocktail DB"""
        pass

    @filter.command(alias="alc")
    async def alcohol(self, ctx, *, query):
        """Filter cocktails by alcohol"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/filter.php?a={query}') as resp:

                    response = await resp.json()
                    data=response.get("drinks")
                    embed=discord.Embed(title=f"List of all alcoholic cocktails",color=discord.Color.random())
                    Pages=[]

                    Cocktails=[]
                    if data != None:
                        for i in data:
                            a=i.get("strDrink")
                            Cocktails.append(a)
                            Pages.append(multipledrinksformatter(i, list(data).index(i)))
                            
                        embed.add_field(name=f"Name: ", value=f"Page Number", inline=False)
                        for i in Cocktails:
                            embed.add_field(name=f"Results: ", value=f"{i} : {Cocktails.index(i)}\n", inline=False)

                        Pages.insert(0, embed)

                        await menu(ctx, Pages, DEFAULT_CONTROLS)
                    else:
                        await ctx.send("No results found")
        except:
            await ctx.send("Invalid parameters. Please use `!cocktail list alcoholic` to see all alcoholic filters")

    @filter.command(alias="cat")
    async def category(self, ctx, *, query):
        """Filter cocktails by category"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/filter.php?c={query}') as resp:

                    response = await resp.json()
                    data=response.get("drinks")
                    embed=discord.Embed(title=f"List of all {query} cocktails",color=discord.Color.random())
                    Pages=[]

                    Cocktails=[]
                    if data != None:
                        for i in data:
                            a=i.get("strDrink")
                            Cocktails.append(a)
                            Pages.append(multipledrinksformatter(i, list(data).index(i)))

                        embed.add_field(name=f"Name: ", value=f"Page Number", inline=False)
                        for i in Cocktails:
                            embed.add_field(name=f"Results: ", value=f"{i} : {Cocktails.index(i)}\n", inline=False)

                        Pages.insert(0, embed)

                        await menu(ctx, Pages, DEFAULT_CONTROLS)
                    else:
                        await ctx.send("No results found")
        except:
            await ctx.send("Invalid parameters. Please use `!cocktail list categories` to see all alcoholic filters")

    @filter.command()
    async def glass(self, ctx, *, query):
        """Filter cocktails by glass"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/filter.php?g={query}') as resp:

                    response = await resp.json()
                    data=response.get("drinks")
                    embed=discord.Embed(title=f"List of all cocktails that use {query}",color=discord.Color.random())
                    Pages=[]

                    Cocktails=[]
                    if data != None:
                        for i in data:
                            a=i.get("strDrink")
                            Cocktails.append(a)
                            Pages.append(multipledrinksformatter(i, list(data).index(i)))

                        embed.add_field(name=f"Name: ", value=f"Page Number", inline=False)
                        for i in Cocktails:
                            embed.add_field(name=f"Results: ", value=f"{i} : {Cocktails.index(i)}\n", inline=False)

                        Pages.insert(0, embed)

                        await menu(ctx, Pages, DEFAULT_CONTROLS)
                    else:
                        await ctx.send("No results found")
        except:
            await ctx.send("Invalid parameters. Please use `!cocktail list glasses` to see all alcoholic filters")


    #LIST COMMANDS
    @cocktail.group()
    async def list(self, ctx: commands.Context):
        """List all entries Catergories/Glasses/Ingredients/Alcoholic for Cocktail DB"""
        pass
    
    @list.command()
    async def catergories(self, ctx: commands.Context):
        """List all categories"""
        categorylist = []
        embed=discord.Embed(color=discord.Color.random())
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/list.php?c=list') as resp:
                
                response = await resp.json()
                if response != None:
                    data=response.get("drinks")
                    for Drink in data:
                        categorylist.append(Drink.get("strCategory"))

                    embed.add_field(name=f"List of all Categories:", value=f"{categorylist}", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No results found")
                
    @list.command()
    async def glasses(self, ctx: commands.Context):
        """List all glasses"""
        glasseslist = []
        embed=discord.Embed(color=discord.Color.random())
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/list.php?g=list') as resp:
                
                response = await resp.json()
                if response != None:
                    data=response.get("drinks")
                    for Glass in data:
                        glasseslist.append(Glass.get("strGlass"))
                    embed.add_field(name=f"List of all Glasses:", value=f"{glasseslist}", inline=False) 
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No results found")

    @list.command()
    async def ingredients(self, ctx: commands.Context):
        """List all ingredients"""
        ingredientlist = []
        embed=discord.Embed(color=discord.Color.random())
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/list.php?i=list') as resp:
                
                response = await resp.json()
                if response != None:
                    data=response.get("drinks")
                    for Ingredient in data:
                        ingredientlist.append(Ingredient.get("strIngredient1"))
                    
                    for i in chunks(ingredientlist,20):
                        embed.add_field(name=f"List of all Ingredients:", value=f"{i}", inline=False) 
                    await ctx.send(embed=embed)

                else:
                    await ctx.send("No results found") 

    @list.command()
    async def alcoholic(self, ctx: commands.Context):
        """List all alcoholic filters"""
        alcoholiclist = []
        embed=discord.Embed(color=discord.Color.random())
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/list.php?a=list') as resp:
                response = await resp.json()
                if response != None:
                    data=response.get("drinks")
                    for Alcoholic in data:
                        alcoholiclist.append(Alcoholic.get("strAlcoholic"))
                    embed.add_field(name=f"List of all Alcoholic Filters:", value=f"{alcoholiclist}", inline=False) 
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No results found")  
                
        

    """ALIAS' REQUESTED"""
    @commands.command()
    async def findcocktail(self, ctx, *, query):
        """Find a cocktail by name"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/search.php?s={query}') as resp:
                
                response = await resp.json()
                data=response.get("drinks")
                if data != None:
                    embed = drinksformatter(data)
                    await ctx.send(embed=embed)

                else:
                    await ctx.send("No results found")

    @commands.command()
    async def listcocktail(self, ctx, query):
        """List all cocktails by name"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.thecocktaildb.com/api/json/v1/1/search.php?f={query}') as resp:
                
                response = await resp.json()
                data=response.get("drinks")
                embed=discord.Embed(title=f"List of all cocktails starting with {query}",color=discord.Color.random())
                Pages=[]
                
                Cocktails=[]
                if data != None:
                    for i in data:
                        a=i.get("strDrink")
                        Cocktails.append(a)
                        Pages.append(multipledrinksformatter(i, list(data).index(i)))

                    embed.add_field(name=f"Name:", value=f"Page Number", inline=False)
                    for i in Cocktails:
                        embed.add_field(name=f"Results:", value=f"{i} : {Cocktails.index(i)}", inline=False)

                    Pages.insert(0, embed)
                    
                    await menu(ctx, Pages, DEFAULT_CONTROLS)
                else:
                    await ctx.send("No results found")

    @commands.command()
    async def randomcocktail(self, ctx: commands.Context):
        """Get a random cocktail"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/random.php') as resp:
            
                response = await resp.json()
                
                data=response.get("drinks")
                embed = drinksformatter(data)
                await ctx.send(embed=embed)
        
    @commands.command()
    async def incocktail(self, ctx, query):
        """Search cocktail by its ingredient"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.thecocktaildb.com/api/json/v1/1/search.php?i={query}') as resp:
                
                response = await resp.json()
                data=response.get("ingredients")
                if data != None:
                    embed = ingredientformatter(data)
                    await menu(ctx, embed, DEFAULT_CONTROLS)
                    
                else:
                    await ctx.send("No results found")  
