import pickle
import logging
from typing import Any, Dict, Optional, Tuple
from . import http


_log = logging.getLogger(__name__)

class ScryfallAgent:
    """
    Makes calls to scryfall but uses local cache where possible.
    """
    def __init__(self, host: str, pretty: bool=False, cachefile='scryfall.p'):
        """Create a new agent for the given scryfall host. The host should be
        the dns name only and should not include the URI scheme. If pretty is
        set, JSON responses will be prettified; disable this for production.
        """
        if host.lower().startswith('http:'):
            host = host[5:]
        elif host.lower().startswith('https:'):
            host = host[6:]
        self._http = http.HttpAgent(host, ssl=True, antiflood_secs=0.3)
        self._pretty_response = pretty
        self._cachefile = cachefile
        self._cache = pathcache()
        
        try:
            with open(cachefile, 'rb') as fp:
                self._cache = pathcache(pickle.load(fp))
        except:
            _log.warn("couldn't load cache file; a new cache will be started")

    def get_card_by_name(self,
            name: str, fuzzy: bool=False, set_code: Optional[str] = None
    ):
        """Get details on a card by name. If fuzzy, fuzzy search is applied. If
        set_code is given, it is a three to five-letter set code that the lookup
        will be limited to."""
        params = {
            'pretty': self._pretty_response
        }
        if fuzzy:
            params['fuzzy'] = name
        else:
            params['exact'] = name
        _, resp = self._http.request('GET', '/cards/named', query=params)
        return resp

    def get_card_by_num(self, set_code: str, number: int, lang: str=None):
        """Get details on a card by its collector's number within a set. If
        lang is given, card in that language is retrieved instead of the english
        one."""

        # check cache first
        cachelang = lang if lang is not None else 'en'
        cachepath = '/sets/{:s}/cards/{:s}/{:s}'.format(normalized_set(set_code), number, cachelang)
        cached, hit = self._cache.get(cachepath)
        if hit:
            return cached

        params = {
            'pretty': self._pretty_response
        }
        lang_url = '/' + lang if lang is not None else ''
        path = '/cards/{:s}/{:s}{:s}'.format(set_code, number, lang_url)
        _, resp = self._http.request('GET', path, query=params)
        
        self._cache.set(cachepath, resp)
        self._save_cache()
        return resp
        
    def _save_cache(self):
        try:
            with open(self._cachefile, 'wb') as fp:
                pickle.dump(self._cache.store, fp)
        except:
            _log.warn("couldn't load cache file; a new cache will be started")


class pathcache:
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

        comps = path.split('/')
        
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

        comps = path.split('/')

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

        comps = path.split('/')

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

    


def normalized_set(set_code: str) -> str:
    return set_code.upper()
