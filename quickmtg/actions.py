from . import scryfall
import pprint

def search_cards(api: scryfall.ScryfallAgent, fuzzy: bool=False, set: str=None, *cards):
    if len(cards) < 1:
        raise TypeError("Need to give at least one card to look up")

    for card in cards:
        repl = api.get_card_by_name(card, fuzzy=fuzzy, set_code=set)
        pprint.pprint(repl)
    
def show_card(api: scryfall.ScryfallAgent, set: str, num: int, lang: str):
    repl = api.get_card_by_num(set, num, lang)
    pprint.pprint(repl)
    
def show_card(api: scryfall.ScryfallAgent, set: str, num: int, lang: str, size: str, back: bool):
    api.get_card_image(set, num, lang, size, back)
    print("card downloaded; check ./.scryfall directory")
    