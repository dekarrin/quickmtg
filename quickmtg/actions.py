from datetime import timedelta
from typing import Any, Dict, Optional
from quickmtg.card import OwnedCard, SizeFull, SizeLarge, SizeSmall, image_slug
from . import scryfall, tappedout, layout, util
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

    _log.info("(1/6) Reading cards from tappedout inventory list...")
    parsed_cards = list()
    with open(list_file, 'r') as fp:
        lineno = 0
        for line in fp:
            lineno += 1
            if line.strip() == '':
                continue
            try:
                c = tappedout.parse_list_line(line)           
            except Exception as e:
                _log.exception("skipping bad line {:d}: problem reading line".format(lineno))
                continue
                
            parsed_cards.append(c)
    
    if len(parsed_cards) < 1:
        _log.error("No cards were successfully processed!")
        return
    
    _log.info("(2/6) Filling incomplete card data with data from scryfall...")
    cards = list()
    show_progress = util.once_every(timedelta(seconds=5), lambda: _log.info(util.progress(cards, parsed_cards)))
    for c in parsed_cards:
        show_progress()
        if c.number == '':
            # need to get the number
            c.number = api.get_card_default_num(c.name, c.set)

        full_data = api.get_card_by_num(c.set, c.number).to_dict()                
        owned = OwnedCard(**full_data)
        owned.foil = c.foil
        owned.condition = c.condition
        owned.count = c.count
        cards.append(owned)

    # cards are now gotten, generate html:
    # 1. gen the html
    _log.info("(3/6) Generating binder pages...")
    rows = 3
    cols = 3
    cards_on_page = rows * cols
    total_pages = int(math.ceil(len(cards) / cards_on_page))
    pageno = 0
    for page in grouper(cards, cards_on_page):
        pageno += 1
        content = layout.gen_binder_page(page, pageno, total_pages, rows, cols)
        file_name = 'binder{:03d}.html'.format(pageno)
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, 'w') as fp:
            fp.write(content)

    # copy the images
    _log.info("(4/6) Copying image data to output directory...")
    steps_done = 0
    # four steps per card because:
    # 1 for get small, 1 for get large,
    # 1 for save small, 1 for save large
    # 1 at the v end is for getting the card back image
    steps_needed = (len(cards) * 4) + 1
    show_progress = util.once_every(timedelta(seconds=5), lambda: _log.info(util.progress(steps_done, steps_needed)))
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
    for c in cards:
        image_data_small = api.get_card_image(c.set, c.number, size=SizeLarge)
        dest_path_small = os.path.join(images_path, image_slug(c, SizeLarge))
        steps_done += 1
        show_progress()
        image_data_full = api.get_card_image(c.set, c.number, size=SizeLarge)
        dest_path_full = os.path.join(images_path, image_slug(c, SizeLarge))
        steps_done += 1
        show_progress()
        with open(dest_path_small, 'wb') as fp:
            fp.write(image_data_small)
        steps_done += 1
        show_progress()
        with open(dest_path_full, 'wb') as fp:
            fp.write(image_data_full)
        steps_done += 1
        show_progress()
    # get back image
    image_data_back, back_fmt = api.get_card_back_image()
    dest_path_back = os.path.join(images_path, 'back.{:s}'.format(back_fmt))
    with open(dest_path_back, 'wb') as fp:
        fp.write(image_data_back)

    # generate an index page
    _log.info("(5/6) Generating index pages...")
    index_content = layout.gen_index_page()
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w') as fp:
        fp.write(index_content)

    _log.info("(6/6) Copying static assets...")
    stylesheet = layout.gen_stylesheet()
    dest_path = os.path.join(assets_path, 'styles.css')
    with open(dest_path, 'w') as fp:
        fp.write(stylesheet)


    _log.info("Done! Page is now ready at {:s}".format(output_dir + '/index.html'))
    