from datetime import timedelta
from typing import Optional, Sequence, Tuple
from ..card import OwnedCard, SizeLarge, image_slug
from .. import scryfall, tappedout, layout, util, storage, binder as qmtgbinder
from ..iterutil import grouper
import logging
import os
import math
import shutil

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def create(store: storage.AutoSaveObjectStore, api: scryfall.ScryfallAgent, list_file: str, output_dir: str, name: str=None, id: str=None):
    id_name = name
    if id is not None:
        id_name = id
    if name is None:
        if id_name is None:
            name = "default"
            id_name = name
            meta, exists = store.get('/binders/.meta')
            if exists:
                num = 0
                while id_name in meta.ids:
                    num += 1
                    id_name = name + '_' + str(num)
        else:
            name = id_name
    
    if name == '':
        _log.error("Can't create a binder with a blank name; either give a value or allow default to be set.")
        return
    
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
    
    cards = sorted(cards)

    # cards are now gotten, generate html:
    _log.info("(3/6) Generating binder pages...")
    _generate_binder_pages(name, output_dir, cards, 3, 3)
    _log.info("(4/6) Copying image data to output directory...")
    _copy_binder_images(api, output_dir, cards)
    _log.info("(5/6) Generating index pages...")
    _generate_binder_index(name, output_dir)
    _log.info("(6/6) Copying static assets...")
    _copy_binder_assets(output_dir)
    
    # dump info about the binder to the directory and main store
    binder = qmtgbinder.Binder(path=output_dir, name=name, id=id_name, cards=cards)
    json_dest = os.path.join(output_dir, 'binder.json')
    binder.to_file(json_dest)
    
    store.batch()
    store.set('/binders/' + binder.id, binder)
    binders_meta, _ = store.get('/binders/.meta', default=qmtgbinder.Metadata())
    binders_meta.ids.add(binder.id)
    store.set('/binders/.meta', binders_meta)
    store.commit()
    
    _log.info("Done! Binder view `{:s}` is now ready at {:s}".format(binder.id, output_dir + '/index.html'))
    
def list_all(store: storage.AutoSaveObjectStore):
    metadata, _ = store.get('/binders/.meta', default=qmtgbinder.Metadata())
    if len(metadata.ids) < 1:
        _log.info("(No binder views have been created yet)")
        return

    for id in sorted(metadata.ids):
        _log.info(id)

def show(store: storage.AutoSaveObjectStore, bid: str, show_cards: bool=False):
    binder, _ = _get_binder_from_store(store, bid)
    if binder is None:
        return

    _log.info("Binder ID: {:s}".format(binder.id))
    _log.info("Name:      {:s}".format(binder.name))
    _log.info("Location:  {:s}".format(binder.path))
    if not show_cards:
        _log.info("Cards:     {:d}".format(len(binder.cards)))
    else:
        _log.info("Cards:")
        for c in binder.cards:
            _log.info("* " + tappedout.to_list_line(c))
    
def edit(store: storage.AutoSaveObjectStore, bid: str, newid: Optional[str]=None, newname: Optional[str]=None, newpath: Optional[str]=None):
    binder, metadata = _get_binder_from_store(store, bid)
    if binder is None:
        return
    
    oldid = binder.id
    updated = False
    if newpath is not None:
        updated = True
        binder.path = newpath
    if newid is not None:
        updated = True
        binder.id = newid
        if binder.id == '':
            _log.error("Can't set ID of binder to blank string")
            return
    if newname is not None:
        updated = True
        binder.name = newname
        if binder.name == '':
            _log.error("Can't set name of binder to blank string")

    if not updated:
        return
    
    store.batch()
    store.set('/binders/' + binder.id, binder)
    if binder.id != oldid:
        store.clear('/binders/' + oldid)
        metadata.ids.remove(oldid)
        metadata.ids.add(binder.id)
        store.set('/binders/.meta', metadata)
    store.commit()

    binder_data_file = os.path.join(binder.path, 'binder.json')
    try:
        curbinder = qmtgbinder.from_file(binder_data_file)
    except Exception as e:
        _log.warning("System qmtg records updated successfully, but could not update binder view directory.")
        _log.warning("{!s}".format(e))
        _log.warning("Update path to point to a valid binder view directory to correct this for the future.")
        return
    else:
        if curbinder.name != binder.name:
            # name has been updated; this requires a regeneration
            _log.info("Name has been updated; regenerating binder view...")
            _log.info("(1/2) Generating binder pages...")
            _generate_binder_pages(binder.name, binder.path, curbinder.cards, 3, 3)
            _log.info("(2/2) Generating index pages...")
            _generate_binder_index(binder.name, binder.path)
            _log.info("Binder pages have been updated with new name")

    try:
        binder.to_file(binder_data_file)
    except Exception as e:
        _log.warning("System qmtg records updated successfully, but could not update binder view directory.")
        _log.warning("{!s}".format(e))
        return

def delete(store: storage.AutoSaveObjectStore, bid: str, delete_built: bool=False):
    binder, metadata = _get_binder_from_store(store, bid)
    if binder is None:
        return

    # got binder and meta, now do operations:
    if delete_built:
        try:
            shutil.rmtree(binder.path)
        except Exception as e:
            _log.warning("couldn't delete binder site directory: {:s}".format(str(e)))
        else:
            _log.info("Deleted built binder view site {:s}".format(binder.path))

    store.batch()
    store.clear('/binders/' + binder.id)
    metadata.ids.remove(bid)
    store.set('/binders/.meta', metadata)
    store.commit()
    _log.info("Deleted binder view `{:s}` from qmtg's system stores.".format(binder.id))

    
def _get_binder_from_store(store: storage.AutoSaveObjectStore, bid: str) -> Tuple[qmtgbinder.Binder, qmtgbinder.Metadata]:
    """
    Get binder from store, checking metadata to ensure all is well with it.

    Returns (binder, metadata) where the binder is specified binder and the
    metadata is the binder metadata object.

    Returns (None, metadata) if the binder could not be obtained. Caller should
    not print any message in this case as it has already been printed. metadata
    will always be returned as non-None even if binder is None. If metadata
    didn't previously exist in the store, an empty metadata object is returned.
    """
    metadata, _ = store.get('/binders/.meta', default=qmtgbinder.Metadata())
    if bid not in metadata.ids:
        _log.error("`{:s}` is not a binder that is currently defined.".format(bid))
        return None, metadata

    binder, exists = store.get('/binders/' + bid)
    if not exists:
        # something is wrong with the store, remove this entry and report an
        # error
        metadata.ids.remove(bid)
        store.set('/binders/.meta', metadata)
        _log.error("`{:s}` was listed in metadata, but couldn't load record. The entry has now been removed from metadata to repair it.".format(bid))
        return None, metadata

    return binder, metadata
    
def _generate_binder_pages(name: str, output_dir: str, cards: Sequence[OwnedCard], rows: int, cols: int):
    cards_on_page = rows * cols
    total_pages = int(math.ceil(len(cards) / cards_on_page))
    pageno = 0
    for page in grouper(cards, cards_on_page):
        pageno += 1
        content = layout.gen_binder_page(page, pageno, total_pages, rows, cols, binder_name=name)
        file_name = 'binder{:03d}.html'.format(pageno)
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, 'w') as fp:
            fp.write(content)

def _copy_binder_images(api: scryfall.ScryfallAgent, output_dir: str, cards: Sequence[OwnedCard]):
    # copy the images
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

def _generate_binder_index(name: str, output_dir: str):
    # generate an index page
    index_content = layout.gen_index_page(binder_name=name)
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w') as fp:
        fp.write(index_content)

def _copy_binder_assets(output_dir: str):
    assets_path = os.path.join(output_dir, 'assets')
    statics = layout.gen_static()
    for f in statics:
        dest_path = os.path.join(assets_path, f['name'])
        with open(dest_path, 'w' + f['write_mode']) as fp:
            fp.write(f['data'])