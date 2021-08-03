import os
import logging
import shutil

from datetime import timedelta
from typing import Optional, Tuple

from .. import scryfall, storage, tappedout, util, inven
from ..card import OwnedCard


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def create(store: storage.AutoSaveObjectStore, output_dir: str, name: str=None, id: str=None):
    id_name = name
    if id is not None:
        id_name = id
    if name is None and id_name is None:
        name = "default"
        id_name = name
        meta, exists = store.get('/inventories/.meta')
        if exists:
            num = 0
            while id_name in meta.ids:
                num += 1
                id_name = name + '_' + str(num)
    
    if name == '':
        _log.error("Can't create an inventory with a blank name; either give a value or allow default to be set.")
        return
    
    try:
        os.mkdir(output_dir)
    except FileExistsError:
        pass  # This is fine
        
    # dump info about the binder to the directory and main store
    inv = inven.Inventory(path=output_dir, name=name, id=id_name)
    json_dest = os.path.join(output_dir, 'inventory.json')
    inv.to_file(json_dest)
    
    store.batch()
    store.set('/inventories/' + inv.id, inv)
    invs_meta, _ = store.get('/inventories/.meta', default=inven.Metadata())
    invs_meta.ids.add(inv.id)
    store.set('/inventories/.meta', invs_meta)
    store.commit()
    
    _log.info("Done! Inventory `{:s}` has now been created in {:s}".format(inv.id, output_dir))
    

def list_all(store: storage.AutoSaveObjectStore):
    metadata, _ = store.get('/inventories/.meta', default=inven.Metadata())
    if len(metadata.ids) < 1:
        _log.info("(No inventories have been created yet)")
        return

    for id in sorted(metadata.ids):
        _log.info(id)

def edit(store: storage.AutoSaveObjectStore, iid: str, newid: Optional[str]=None, newname: Optional[str]=None, newpath: Optional[str]=None):
    inv, metadata = _get_inv_from_store(store, iid)
    if inv is None:
        return
    
    oldid = inv.id
    updated = False
    if newpath is not None:
        updated = True
        inv.path = newpath
    if newid is not None:
        updated = True
        inv.id = newid
        if inv.id == '':
            _log.error("Can't set ID of inventory to blank string")
            return
    if newname is not None:
        updated = True
        inv.name = newname
        if inv.name == '':
            _log.error("Can't set name of inventory to blank string")

    if not updated:
        return
    
    store.batch()
    store.set('/inventories/' + inv.id, inv)
    if inv.id != oldid:
        store.clear('/inventories/' + oldid)
        metadata.ids.remove(oldid)
        metadata.ids.add(inv.id)
        store.set('/inventories/.meta', metadata)
    store.commit()

    inv_data_file = os.path.join(inv.path, 'inventory.json')
    try:
        inv.to_file(inv_data_file)
    except Exception as e:
        _log.warning("System qmtg records updated successfully, but could not update inventory directory.")
        _log.warning("{!s}".format(e))

def show(store: storage.AutoSaveObjectStore, iid: str, show_cards: bool=False, board_format: bool=False, no_meta: bool=False):
    inv, _ = _get_inv_from_store(store, iid)
    if inv is None:
        return

    if not no_meta:
        _log.info("Inventory ID: {:s}".format(inv.id))
        _log.info("Name:         {:s}".format(inv.name))
        _log.info("Location:     {:s}".format(inv.path))
    
    if not show_cards:
        _log.info("Cards:        {:d}".format(len(inv.cards)))
    else:
        if not no_meta:
            _log.info("Cards:")
        
        for c in inv.cards:
            if board_format:
                _log.info(tappedout.to_list_line(c))
            else:
                _log.info('{:s}'.format(c))

def delete(store: storage.AutoSaveObjectStore, iid: str, delete_built: bool=False):
    inv, metadata = _get_inv_from_store(store, iid)
    if inv is None:
        return

    # got binder and meta, now do operations:
    if delete_built:
        shutil.rmtree(inv.path)
        _log.info("Deleted built inventory directory {:s}".format(inv.path))

    store.batch()
    store.clear('/inventories/' + inv.id)
    metadata.ids.remove(iid)
    store.set('/inventories/.meta', metadata)
    store.commit()
    _log.info("Deleted inventory `{:s}` from qmtg's system stores.".format(inv.id))


def addcards(store: storage.AutoSaveObjectStore, api: scryfall.ScryfallAgent, iid: str, *list_files: str):
    inv, metadata = _get_inv_from_store(store, iid)
    if inv is None:
        return

    if len(list_files) < 1:
        raise ValueError("cannot add cards from empty set of card list files")
    
    cards_to_add = list()
    for cardlist in list_files:
        _log.info("Reading cards from tappedout inventory list {:s}...".format(cardlist))
        
        try:
            parsed_cards = tappedout.parse_list_file(cardlist)
        except ValueError as e:
            _log.exception("Problem reading file {:s}: {:s}".format(cardlist, str(e)))
            _log.error("Could not read {:s}".format(cardlist))
            return
        
        _log.info("  Filling incomplete card data in list with data from scryfall...")
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
            cards_to_add.append(owned)

    _log.info("Done reading cards, now adding...".format(cardlist))  
    for c in cards_to_add:
        inv.add_card(c, ['storage',] * c.count)
    
    store.set('/inventories/' + inv.id, inv)

    inv_data_file = os.path.join(inv.path, 'inventory.json')
    try:
        inv.to_file(inv_data_file)
    except Exception as e:
        _log.warning("System qmtg records updated successfully, but could not update inventory directory.")
        _log.warning("{!s}".format(e))

    _log.info("Finished adding cards to inventory `{:s}`".format(iid))
    

def _get_inv_from_store(store: storage.AutoSaveObjectStore, iid: str) -> Tuple[inven.Inventory, inven.Metadata]:
    """
    Get inventory from store, checking metadata to ensure all is well with it.

    Returns (inventory, metadata) where the inventory is specified inventory and
    the metadata is the inventory metadata object.

    Returns (None, metadata) if the inventory could not be obtained. Caller should
    not print any message in this case as it has already been printed. metadata
    will always be returned as non-None even if inventory is None. If metadata
    didn't previously exist in the store, an empty metadata object is returned.
    """
    metadata, _ = store.get('/inventories/.meta', default=inven.Metadata())
    if iid not in metadata.ids:
        _log.error("`{:s}` is not an inventory that is currently defined.".format(iid))
        return None, metadata

    inv, exists = store.get('/inventories/' + iid)
    if not exists:
        # something is wrong with the store, remove this entry and report an
        # error
        metadata.ids.remove(iid)
        store.set('/inventories/.meta', metadata)
        _log.error("`{:s}` was listed in metadata, but couldn't load record. The entry has now been removed from metadata to repair it.".format(iid))
        return None, metadata

    return inv, metadata
