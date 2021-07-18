import html
import os
import pickle
import logging
from posixpath import join
import uuid
from quickmtg.card import Card, Face
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
from . import http


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

class ScryfallAgent:
    """
    Makes calls to scryfall but uses local cache where possible.
    """
    def __init__(self, host: str, pretty: bool=False, cachefile: str='scryfall.p', file_home: str='.scryfall'):
        """Create a new agent for the given scryfall host. The host should be
        the dns name only and should not include the URI scheme. If pretty is
        set, JSON responses will be prettified; disable this for production.
        """
        if host.lower().startswith('http:'):
            host = host[5:]
        elif host.lower().startswith('https:'):
            host = host[6:]
        self._http = http.HttpAgent(host, ssl=True, antiflood_secs=0.3)
        self._picshttp = http.HttpAgent(host, ssl=True, antiflood_secs=0.3, response_payload='binary', ignored_errors=[422, 404])
        self._pretty_response = pretty
        self._cachefile = cachefile
        self._cache = _PathCache()
        self._filestore = _FileCache(file_home)
        
        try:
            with open(cachefile, 'rb') as fp:
                data = pickle.load(fp)
            if 'requests' not in data:
                data['requests'] = data
                data['files'] = dict()

            self._cache = _PathCache(existing_store=data['requests'])
            self._filestore = _FileCache(file_home, existing_store=data['files'])
        except:
            _log.warn("couldn't load cache file; a new cache will be started")
            # start one so we dont get another warning
            self._save_cache()

    def get_card_by_name(self,
            name: str, fuzzy: bool=False, set_code: Optional[str] = None
    ) -> Card:
        """Get details on a card by name. If fuzzy, fuzzy search is applied. If
        set_code is given, it is a three to five-letter set code that the lookup
        will be limited to."""

        set_code = set_code.lower()

        params = {
            'pretty': self._pretty_response
        }
        if fuzzy:
            params['fuzzy'] = name
        else:
            params['exact'] = name

        if set_code is not None:
            params['set'] = set_code
        
        _, resp = self._http.request('GET', '/cards/named', query=params)
        c = _parse_resp_card(resp)
        return c
    
    def search_cards(self,
            name: Optional[str], exact: bool=False, set_code: Optional[str]=None
    ) -> List[Card]:
        """Search for cards that match the given criterea. Only one result per
        unique matching functionality is returned unless it is limited to the
        set.
        
        Results will always be sorted as set/collector num, ascending.
        """

        set_code = set_code.lower()
        q = build_search_query(name=name, exact=exact, set=set_code)
        params = {
            'pretty': self._pretty_response,
            'q': q,
            'unique': 'prints' if set_code is not None else 'cards',
            'order': 'set',
            'dir': 'asc',
        }
        
        _, resp = self._http.request('GET', '/cards/search', query=params)
        results = list()

        if 'data' not in resp:
            raise TypeError("response from scryfall did not contain a results list")
        
        for r in resp['data']:
            c = _parse_resp_card(r)
            results.append(c)

        return results

    def get_card_image(self, set_code: str, number: str, lang: str=None, size='full', back=False) -> Tuple[bytes, str]:
        """Get image on a card by its collector's number within a set. If
        lang is given, card in that language is retrieved instead of the english
        one.
        
        Size can be specified. It can be either 'full', 'small', 'normal', or
        'large', and defaults to full.

        Returns image bytes, and file type as either "jpg" or "png". Calling at
        least once ensures it is created and locally cached for future calls.
        """
        set_code = set_code.lower()
        cachelang = lang if lang is not None else 'en'
        img_format = 'png' if size.lower() == 'full' else 'jpg'
        frontback = 'back' if back else 'front'

        num_padded = number
        try:
            only_int = int(number)
            num_padded = '{:03d}'.format(only_int)
        except TypeError:
            pass

        cachepath = '/images/set-{0:s}/card-{1:s}/{0:s}-{1:s}-{2:s}-{3:s}-{4:s}.{5:s}'.format(set_code, num_padded, frontback, size.lower(), cachelang, img_format)

        file_data, exists = self._filestore.get(cachepath)
        if exists:
            _log.info('already downloaded file, not downloading again')
            return file_data[0], img_format

        # otherwise, need to make the scryfall call
        lang_url = '/' + lang if lang is not None else ''
        path = '/cards/{:s}/{:s}{:s}'.format(set_code, number, lang_url)
        params = {
            'version': 'png' if size.lower() == 'full' else size.lower(),
            'format': 'image'
        }
        if back:
            params['face'] = 'back'
        
        status, resp = self._picshttp.request('GET', path, query=params)
        if status == 422:
            raise ValueError('Card does not have a back face: {:s}:{:03d}'.format(set_code, number))
        if status == 404:
            raise ValueError('Card does not exist in scryfall: {:s}:{:03d}'.format(set_code, number))
        self._filestore.set(cachepath, resp)
        self._save_cache()

    def get_card_by_num(self, set_code: str, number: str, lang: str=None) -> Card:
        """Get details on a card by its collector's number within a set. If
        lang is given, card in that language is retrieved instead of the english
        one."""

        set_code = set_code.lower()

        # check cache first
        cachelang = lang if lang is not None else 'en'
        cachepath = '/sets/{:s}/cards/{:s}/{:s}'.format(set_code, number, cachelang)
        cached, hit = self._cache.get(cachepath)
        if hit:
            return Card(**cached)

        params = {
            'pretty': self._pretty_response
        }
        lang_url = '/' + lang if lang is not None else ''
        path = '/cards/{:s}/{:s}{:s}'.format(set_code, number, lang_url)
        _, resp = self._http.request('GET', path, query=params)
        c = _parse_resp_card(resp)
        
        self._cache.set(cachepath, c.to_dict())
        self._save_cache()
        return c
        
    def _save_cache(self):
        try:
            with open(self._cachefile, 'wb') as fp:
                pickle.dump({
                    'requests': self._cache.store,
                    'files': self._filestore.store
                }, fp)
        except:
            _log.warn("couldn't load cache file; a new cache will be started")


class _PathCache:
    def __init__(self, existing_store: Optional[Dict]=None):
        self._store = dict()
        if existing_store is not None:
            self._store = dict(existing_store)

    def clear(self, path: str):
        """
        Clear all entries at the given path recursively.
        """
        path = path.lstrip('/')

        if path == '':
            self._store = dict()

        comps = list(path.split('/'))
        
        # if any part of the path does not exist, already done
        search = self._store
        for c in comps[:-1]:
            if c not in search:
                return
            search = search[c]

        # check for the actual comp to delete
        if comps[-1] in search:
            del search[comps[-1]]

    def reset(self):
        """Remove all entries and reset the cache."""
        self._store = dict()

    def set(self, path: str, value: Any):
        """Set the value at the given path. If it doesn't yet exist, it is created."""
        path = path.lstrip('/')

        if path == '':
            raise TypeError("Empty or root as path is invalid")

        comps = list(path.split('/'))

        cur = self._store
        navpath = ''
        for c in comps[:-1]:
            navpath += '/' + c
            if c not in cur:
                cur[c] = dict()
            if not isinstance(cur[c], dict):
                raise TypeError("Invalid path: object at {!r} is not a dict".format(navpath))
            cur = cur[c]
        
        # now add the actual item
        cur[comps[-1]] = value

    def get(self, path: str) -> Tuple[Any, bool]:
        """Get the item at the given path. If it doesn't exist, (None, False) is
        returned; otherwise (value, True) is returned where value is the value
        stored at that path."""
        path = path.lstrip('/')

        if path == '':
            raise TypeError("Empty or root as path is invalid")

        comps = list(path.split('/'))

        cur = self._store
        navpath = ''
        for c in comps[:-1]:
            navpath += '/' + c
            if c not in cur:
                return (None, False)
            if not isinstance(cur[c], dict):
                raise TypeError("Invalid path: object at {!r} is not a dict".format(navpath))
            cur = cur[c]

        if comps[-1] not in cur:
            return (None, False)
        return (cur[comps[-1]], True)

    @property
    def store(self) -> dict:
        """Return the store as a dict, for pickling."""
        return self._store

    
class _FileCache(_PathCache):
    def __init__(self, root_dir: str, existing_store: Optional[Dict]=None):
        super().__init__(existing_store)
        self._root = root_dir
        
        try:
            os.mkdir(root_dir)
        except FileExistsError:
            pass
            # It's fine if it already exists
        
        if not os.path.isdir(root_dir):
            raise ValueError("{!r} does not exist for local file cache".format(root_dir))

    def reset(self):
        """Delete all local files to reset the cache."""
        self.clear('/')

    def clear(self, path: str):
        """
        Clear all entries at the given path recursively.
        """
        path = path.strip('/')
        if path == '':
            start = self._store
        else:
            comps = list(path.split('/'))
            cur = self._store
            for p in comps:
                if p not in cur:
                    # we are done, it's already clear
                    super().clear(path)
                    return
                cur = cur[p]
            start = cur

        _recurse(lambda path, _: os.unlink(path), start, self._root)
        super().clear(path)

    def set(self, path: str, value: bytes):
        """Set the file at the given path. If it doesn't yet exist, it is
        created, as is any parent directories"""
        joined_path = '/'.join([self._root.rstrip('/'), path.lstrip('/')])
        full_path = os.path.abspath(joined_path)
        size = len(value)
        super().set(path, {'filepath': full_path, 'size': size})

        norm_path = path.strip('/')
        if norm_path == '':
            # it won't be, that's not allowed by super().set(), but double check anyways
            raise ValueError('Path cannot be root or empty')
        
        comps = norm_path.split('/')
        partial_path = self._root
        try:
            for c in comps[:-1]:
                partial_path = os.path.join(partial_path, c)
                try:
                    os.mkdir(partial_path)
                except FileExistsError:
                    pass
                    # this is fine, just dont create the dir
            
            # okay, now actually create the file, since parent dirs have been
            # made
            with open(full_path, 'wb') as fp:
                fp.write(value)
        except:
            super().clear(path)
            raise
    
    def get(self, path: str) -> Tuple[Tuple[bytes, Any], bool]:
        """Get the file at the given path. If it doesn't exist, (None, False) is
        returned; otherwise ((filebytes, metadata), True) is returned where
        value is the value stored at that path."""
        meta, exists = super().get(path)
        if not exists:
            return None, False
        
        filepath = meta['filepath']
        size = meta['size']

        with open(filepath, 'rb') as fp:
            data = fp.read(size)
        
        return (data, meta), True


def _recurse(leaf_fn: Callable[[str, Any], Any], obj: Union[str, Dict[str, Any]], cur_path: str):
    """Recurse on file-like paths, dont really care about the values"""
    if isinstance(obj, dict):
        for k in obj:
            full_path = os.path.join(cur_path, k)
            _recurse(leaf_fn, obj[k], full_path)
    else:
        leaf_fn(cur_path, obj)
    

def _parse_resp_face(f: Dict[str, Any]) -> Face:
    face = Face(
        name=f['name'],
        type=f['type_line'],
        cost=f['mana_cost'],
        text=f.get('oracle_text', ''),
        power=f.get('power', None),
        toughness=f.get('toughness', None)
    )
    return face


def _parse_resp_card(resp: Dict[str, Any]) -> Card:
    c = Card(
        id=uuid.UUID(resp['id']),
        set=resp['set'],
        rarity=resp['rarity'],
        number=resp['collector_number']
    )

    # must parse each face
    layout = resp['layout']
    if layout in ['split', 'flip', 'transform', 'double_faced_token']:
        for f in resp['card_faces']:
            face = _parse_resp_face(f)
            c.faces.append(face)
    else:
        face = _parse_resp_face(resp)
        c.faces.append(face)

    return c


def build_search_query(name: str=None, set: str=None, exact: bool=False):
    q = ""
    if name is not None:
        if exact:
            name = name.replace('\\', '\\\\').replace('"', '\\"')
            q += ' !"' + name + '"'
        else:
            q += ' ' + name

    if set is not None:
        q += ' set:' + set

    
    return q.strip()
