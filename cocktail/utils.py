import discord
from redbot.core.utils.chat_formatting import pagify


def drinksformatter(data):
    data = data[0]
    ingredients = []
    embed = discord.Embed(color=discord.Color.random())

    for i in range(15):
        ingredient = data.get(f"strIngredient{i}")
        measure = data.get(f"strMeasure{i}")

        if ingredient != None:
            ingredients.append({ingredient, measure})

        else:
            continue

    embed.add_field(name="Name:", value=data.get("strDrink"), inline=False)
    embed.add_field(name="Drink ID:", value=data.get("idDrink"), inline=False)
    embed.add_field(
        name="Altername Drink:", value=data.get("strDrinkAlternate"), inline=False
    )
    embed.add_field(name="Category:", value=data.get("strCategory"), inline=False)
    embed.add_field(name="Alcoholic:", value=data.get("strAlcoholic"), inline=False)
    embed.add_field(name="Glass", value=data.get("strGlass"), inline=False)
    embed.add_field(
        name="Instructions:", value=data.get("strInstructions"), inline=False
    )
    embed.set_footer(text=f"Date modified = {data.get('dateModified')}")

    embed.set_thumbnail(url=data.get("strDrinkThumb"))

    for i in ingredients:

        i = list(i)  ##

        if i != [""]:
            embed.add_field(name=i[0], value=i[1], inline=True)
        else:
            continue
    return embed


def multipledrinksformatter(data, page):
    ingredients = []

    embed = discord.Embed(
        title=f"{data.get('strDrink')}",
        description=f"Page No: {page}",
        color=discord.Color.random(),
    )

    for i in range(15):
        ingredient = data.get(f"strIngredient{i}")
        measure = data.get(f"strMeasure{i}")

        if ingredient != None:
            ingredients.append({ingredient, measure})

        else:
            continue

    embed.add_field(name="Name:", value=data.get("strDrink"), inline=False)
    embed.add_field(name="Drink ID:", value=data.get("idDrink"), inline=False)
    embed.add_field(
        name="Altername Drink:", value=data.get("strDrinkAlternate"), inline=False
    )
    embed.add_field(name="Category:", value=data.get("strCategory"), inline=False)
    embed.add_field(name="Alcoholic:", value=data.get("strAlcoholic"), inline=False)
    embed.add_field(name="Glass", value=data.get("strGlass"), inline=False)
    embed.add_field(
        name="Instructions:", value=data.get("strInstructions"), inline=False
    )
    embed.set_footer(text=f"Date modified = {data.get('dateModified')}")

    embed.set_thumbnail(url=data.get("strDrinkThumb"))

    for i in ingredients:

        i = list(i)  ##

        if i != [""]:
            embed.add_field(name=i[0], value=i[1], inline=True)
        else:
            continue

    return embed


def ingredientformatter(data):
    data = data[0]
    pages = []

    page1 = discord.Embed(color=discord.Color.random())
    page1.add_field(name="Name:", value=data.get("strIngredient"), inline=False)
    page1.add_field(name="Ingredient ID:", value=data.get("idIngredient"), inline=False)
    page1.add_field(name="Type:", value=data.get("strType"), inline=False)
    page1.add_field(name="Alcoholic:", value=data.get("strAlcohol"), inline=False)
    page1.add_field(name="ABV score:", value=data.get("strABV"), inline=False)
    page1.set_image(
        url=f"https://www.thecocktaildb.com/images/ingredients/{data.get('strIngredient')}.png"
    )

    pages.append(page1)

    page2 = discord.Embed(color=discord.Color.random())
    for i in list(
        pagify(
            text=(data.get("strDescription")).strip("\r"),
            delims=["\n"],
            page_length=1024,
        )
    ):
        page2.add_field(name="Description:", value=i, inline=False)

    pages.append(page2)

    return pages


def chunks(lst, n):
    """Yield successive n-sized chunks from list."""
    # Stolen from stackoverflow
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
