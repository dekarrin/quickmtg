import logging
import pprint
from .. import scryfall

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def search(api: scryfall.ScryfallAgent, fuzzy: bool=False, set: str=None, *cards):
    if len(cards) < 1:
        raise TypeError("Need to give at least one card to look up")

    for card in cards:
        repl = api.get_card_by_name(card, fuzzy=fuzzy, set_code=set)
        _log.info(pprint.pprint(repl))
    
def show(api: scryfall.ScryfallAgent, set: str, num: str, lang: str):
    repl = api.get_card_by_num(set, num, lang)
    _log.info(pprint.pformat(repl))
    
def get_image(api: scryfall.ScryfallAgent, set: str, num: str, lang: str, size: str, back: bool):
    api.get_card_image(set, num, lang, size, back)
    _log.info("card downloaded; check ./.scryfall directory")
