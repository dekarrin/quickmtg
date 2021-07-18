from quickmtg.card import OwnedCard
from . import scryfall, tappedout
import pprint
import os

def search_cards(api: scryfall.ScryfallAgent, fuzzy: bool=False, set: str=None, *cards):
    if len(cards) < 1:
        raise TypeError("Need to give at least one card to look up")

    for card in cards:
        repl = api.get_card_by_name(card, fuzzy=fuzzy, set_code=set)
        pprint.pprint(repl)
    
def show_card(api: scryfall.ScryfallAgent, set: str, num: int, lang: str):
    repl = api.get_card_by_num(set, num, lang)
    pprint.pprint(repl)
    
def get_card_image(api: scryfall.ScryfallAgent, set: str, num: int, lang: str, size: str, back: bool):
    api.get_card_image(set, num, lang, size, back)
    print("card downloaded; check ./.scryfall directory")

def create_view(api: scryfall.ScryfallAgent, list_file: str, output_dir: str):
    try:
        os.mkdir(output_dir)
    except FileExistsError:
        pass  # This is fine

    cards = list()
    with open(list_file, 'r') as fp:
        lineno = 0
        for line in fp:
            lineno += 1
            try:
                count, c = tappedout.parse_list_line(line)

                if c.number == '':
                    # need to get the number
                    candidates = api.search_cards(name=c.name, exact=True, set_code=c.set)
                    c.number = candidates[0].number

                full_data = api.get_card_by_num(c.set, c.number).to_dict()                
                owned = OwnedCard(**full_data)
                owned.foil = c.foil
                owned.condition = c.condition
                c = owned
                cards.append({
                    'card': c,
                    'count': count
                })
            except Exception as e:
                print("problem reading line {:d} of tappedout list so skipping line: {:s}".format(lineno, str(e)))
    
    print("Updated list:")
    for c in cards:
        print(tappedout.to_list_line(c['count'], c['card']))
    