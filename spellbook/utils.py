
def listformatter(listtoformat):
    
    FilterCharacters=["[", "]"]
    for i in FilterCharacters:
        listtoformat = str(listtoformat).replace(i, "")

    if listtoformat.startswith(", "):
        listtoformat = listtoformat[2:]
    
    if listtoformat.endswith(", "):
        listtoformat = listtoformat[:-2]
    
    return listtoformat