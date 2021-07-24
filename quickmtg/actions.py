from typing import Any, Dict, Optional
from quickmtg.card import OwnedCard, SizeFull, SizeSmall, image_slug
from . import scryfall, tappedout, layout
from .iterutil import grouper
import logging
import pprint
import os
import math
import sys

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def search_cards(api: scryfall.ScryfallAgent, fuzzy: bool=False, set: str=None, *cards):
    if len(cards) < 1:
        raise TypeError("Need to give at least one card to look up")

    for card in cards:
        repl = api.get_card_by_name(card, fuzzy=fuzzy, set_code=set)
        _log.info(pprint.pprint(repl))
    
def show_card(api: scryfall.ScryfallAgent, set: str, num: str, lang: str):
    repl = api.get_card_by_num(set, num, lang)
    _log.info(pprint.pformat(repl))
    
def get_card_image(api: scryfall.ScryfallAgent, set: str, num: str, lang: str, size: str, back: bool):
    api.get_card_image(set, num, lang, size, back)
    _log.info("card downloaded; check ./.scryfall directory")

def create_view(api: scryfall.ScryfallAgent, list_file: str, output_dir: str):
    try:
        os.mkdir(output_dir)
    except FileExistsError:
        pass  # This is fine

    _log.info("(1/4) Reading card data from inventory list and scryfall...")
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
                _log.exception("problem reading line {:d}", lineno)
                print("problem reading line {:d} of tappedout list so skipping line: {:s}".format(lineno, str(e)))

    if len(cards) < 1:
        print("ERROR: No cards were successfully processed!", file=sys.stderr)

    # cards are now gotten, generate html:
    # 1. gen the html
    print("(2/4) Generating binder pages...")
    rows = 3
    cols = 3
    cards_on_page = rows * cols
    pageno = 0
    for page in grouper(cards, cards_on_page):
        pageno += 1
        content = layout.gen_binder_page(page, pageno, rows, cols)
        file_name = 'binder{:03d}.html'.format(pageno)
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, 'w') as fp:
            fp.write(content)

    # 2. copy the images
    print("(3/4) Copying image data (this may take awhile)...")
    assets_path = os.path.join(output_dir, 'assets')
    try:
        os.mkdir(assets_path)
    except FileExistsError:
        pass  # This is fine
    images_path = os.path.join(assets_path, 'images')
    try:
        os.mkdir(images_path)
    except FileExistsError:
        pass  # This is fine
    for cdata in cards:
        c = cdata['card']
        image_data_small = api.get_card_image(c.set, c.number, size=SizeSmall)
        dest_path_small = os.path.join(images_path, image_slug(c, SizeSmall))
        image_data_full = api.get_card_image(c.set, c.number, size=SizeFull)
        dest_path_full = os.path.join(images_path, image_slug(c, SizeFull))
        with open(dest_path_small, 'wb') as fp:
            fp.write(image_data_small)
        with open(dest_path_full, 'wb') as fp:
            fp.write(image_data_full)

    # 3. generate an index page
    print("(4/4) Generating index pages...")
    index_content = layout.gen_index_page()
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w') as fp:
        fp.write(index_content)

    print("Done! Page is now ready at {:s}".format(output_dir + 'index.html'))
    