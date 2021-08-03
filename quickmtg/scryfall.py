from datetime import time, timedelta
import os
import pickle
import logging
import dateutil
from quickmtg import mtgset
import uuid
from .card import Card, Face
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
from . import http, card, storage


_STATIC_CACHE_TTL = timedelta(days=7)
_BACK_IMAGE_URI = 'https://c2.scryfall.com/file/scryfall-errors/missing.jpg'


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class APIError(Exception):
    """
    Represents an error returned by the Scryfall API.
    """
    def __init__(self, message: str, http_code: int=0, warnings: Sequence[str]=None):
        if message is None:
            message = "Scryfall API returned an error"

        if warnings is None:
            warnings = list()

        super().__init__(message)
        self.code = http_code
        self.message = message
        self.warnings = warnings

    def __str__(self) -> str:
        s = self.message
        if len(self.warnings) > 0:
            warn = '('
            for w in self.warnings:
                warn += '{:s}; '.format(w)
            warn = warn[:-2]
            warn += ')'
            s += ' ' + warn
        return s

    def is_not_found(self):
        return self.code == 404

    def is_bad_request(self):
        return self.code == 404

    def is_invalid_face(self):
        return self.code == 422

    @staticmethod
    def parse(resp: Dict[str, Any]) -> 'APIError':
        if 'object' not in resp:
            raise KeyError("Cannot parse error response: response does not contain 'object' key")
        if resp['object'] != 'error':
            raise TypeError("Cannot parse error response: object type is {!r}, not \"error\"".format(resp['object']))

        try:
            status = int(resp['status'])
        except TypeError:
            raise TypeError("Cannot parse error response: 'status' is not an integer")

        warnings = None
        if 'warnings' in resp and resp['warnings'] is not None:
            warnings = list(resp['warnings'])

        details = resp['details']

        return APIError(details, status, warnings)


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
        self._http = http.HttpAgent(host, ssl=True, antiflood_secs=0.2, ignored_errors=[400, 401, 403, 404, 422, 500], log_full_response=False)
        self._pretty_response = pretty
        self._cachefile = cachefile
        self._cache = storage.PathCache()
        self._filestore = storage.FileCache(file_home)
        
        try:
            with open(cachefile, 'rb') as fp:
                data = pickle.load(fp)
            if 'requests' not in data:
                data['requests'] = data
                data['files'] = dict()

            self._cache = storage.PathCache(existing_store=data['requests'])
            self._filestore = storage.FileCache(file_home, existing_store=data['files'])
        except:
            _log.warn("couldn't load cache file; a new cache will be started")
            # start one so we dont get another warning
            self._save_cache()

    def get_catalog_creature_types(self) -> List[str]:
        """
        Get a current list of all creature types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('creature-types')

    def get_catalog_plainswalker_types(self) -> List[str]:
        """
        Get a current list of all plainswalker types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('plainswalker-types')

    def get_catalog_land_types(self) -> List[str]:
        """
        Get a current list of all land types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('land-types')

    def get_catalog_artifact_types(self) -> List[str]:
        """
        Get a current list of all artifact types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('artifact-types')

    def get_catalog_enchantment_types(self) -> List[str]:
        """
        Get a current list of all enchantment types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('enchantment-types')

    def get_catalog_spell_types(self) -> List[str]:
        """
        Get a current list of all spell types. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('spell-types')

    def get_catalog_keyword_abilities(self) -> List[str]:
        """
        Get a current list of all keyword abilities. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('keyword-abilities')

    def get_catalog_keyword_actions(self) -> List[str]:
        """
        Get a current list of all keyword actions. Cached up to _STATIC_CACHE_TTL
        amount of time.
        """
        return self._get_catalog('keyword-actions')

    def _get_catalog(self, catalog_type: str) -> List[str]:
        cachepath = '/static/' + catalog_type
        cached, hit = self._cache.get(cachepath)
        if hit:
            age = time.now() - cached['retrieval_time']
            if age > _STATIC_CACHE_TTL:
                _log.debug('Cache age for {:s} is too old so removing from cache'.format(cachepath))
                self._cache.clear(cachepath)
            else:
                return cached['data']

        _log.debug('Cache miss for {:s}; retrieving from scryfall...'.format(cachepath))

        params = {
            'pretty': self._pretty_response
        }
        
        status, resp = self._http.request('GET', '/catalog/' + catalog_type, query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err

        entries = list(resp['data'])
        self._cache.set(cachepath, {'retrieval_time': time.now(), 'data': entries})
        self._save_cache()

        return entries
    
    def search_cards(self,
            name: Optional[str], exact: bool=False, set_code: Optional[str]=None
    ) -> List[Card]:
        """Search for cards that match the given criterea. Only one result per
        unique matching functionality is returned unless it is limited to the
        set.
        
        Results will always be sorted as set/collector num, ascending.
        
        Raises APIError if there is an issue with the request.

        Due to search results changing frequently based on the state of all
        currently released cards, this function is never cacheable, so it should
        only be called directly when necessary.
        """

        set_code = set_code.lower()
        q = build_search_query(name=name, exact=exact, set=set_code)
        _log.debug("search query: {!r}".format(q))
        params = {
            'pretty': self._pretty_response,
            'q': q,
            'unique': 'prints' if set_code is not None else 'cards',
            'order': 'set',
            'dir': 'asc',
        }
        
        status, resp = self._http.request('GET', '/cards/search', query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err
        
        results = list()

        if 'data' not in resp:
            raise TypeError("response from scryfall did not contain a results list")
        
        for r in resp['data']:
            c = _parse_resp_card(r)
            results.append(c)

        return results

    def get_card_by_name(self,
            name: str, fuzzy: bool=False, set_code: Optional[str] = None
    ) -> Card:
        """Get details on a card by name. If fuzzy, fuzzy search is applied. If
        set_code is given, it is a three to five-letter set code that the lookup
        will be limited to.
        
        Raises APIError if there is an issue with the request.
        """

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
        
        status, resp = self._http.request('GET', '/cards/named', query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err

        c = _parse_resp_card(resp)
        return c
    
    def get_card_by_id(self, sid: uuid.UUID) -> Card:
        """
        Get details on a card by its scryfall ID.
        
        Raises APIError if there is an issue with the request.
        """

        # check cache first, to see if we can just get the setnum-based ID
        self.get_card_by_num
        cachepath = '/id-map/cards/scryfall/{:s}'.format(str(sid))
        cached, hit = self._cache.get(cachepath)
        if hit:
            set_code = cached['set']
            num = cached['num']
            lang = cached['lang']
            return self.get_card_by_num(set_code, num, lang)

        _log.debug('Data cache miss for Scryfall ID {:s}; retrieving from scryfall...'.format(cachepath))

        params = {
            'pretty': self._pretty_response
        }
        path = '/cards/{:s}'.format(str(sid))
        status, resp = self._http.request('GET', path, query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err
        
        c = _parse_resp_card(resp)

        # our cachepath only gives an id mapping; the 'real' cache is in set-num-lang based
        # index.
        setnum_cachepath = '/sets/{:s}/cards/{:s}/{:s}'.format(c.set, c.number, c.language)
        self._cache.set(setnum_cachepath, c.to_dict())
        self._cache.set(cachepath, {'set': c.set, 'num': c.number, 'lang': c.language})
        self._save_cache()
        
        return c
    
    def get_card_by_num(self, set_code: str, number: str, lang: str=None) -> Card:
        """
        Get details on a card by its collector's number within a set. If
        lang is given, card in that language is retrieved instead of the english
        one.
        
        Raises APIError if there is an issue with the request.
        """

        set_code = set_code.lower()

        # check cache first
        cachelang = lang if lang is not None else 'en'
        cachepath = '/sets/{:s}/cards/{:s}/{:s}'.format(set_code, number, cachelang)
        cached, hit = self._cache.get(cachepath)
        if hit:
            return Card(**cached)

        _log.debug('Data cache miss for {:s}; retrieving from scryfall...'.format(cachepath))

        params = {
            'pretty': self._pretty_response
        }
        lang_url = '/' + lang if lang is not None else ''
        path = '/cards/{:s}/{:s}{:s}'.format(set_code, number, lang_url)
        status, resp = self._http.request('GET', path, query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err
        
        c = _parse_resp_card(resp)
        
        self._cache.set(cachepath, c.to_dict())
        # also set the ID mapping so calls to getting card by scryfall ID can get
        # the correct one
        self._cache.set('/id-map/cards/scryfall/' + str(c.id), {
            'set': c.set,
            'num': c.number,
            'lang': c.language
        })

        self._save_cache()
        return c
    
    def get_card_default_num(self, name: str, set_code: str) -> str:
        """
        Gets the default number for a card in a set when none is given. For
        example, get_default_num("Alpine Watchdog", "M21") gives the number that
        should be assumed for a card called 'Alpine Watchdog' in the set Core
        2021 for when it does not specify a particular number.

        This function caches results. If the default number cannot be found in
        the cache, the search API is used to find it. It is then stored in the
        cache for future calls.
        """
        set_code = set_code.lower()

        cachename = name.lower().replace(' ', '_')
        cachepath = '/sets/{:s}/defaults/{:s}'.format(set_code, cachename)
        cached, hit = self._cache.get(cachepath)
        if hit:
            return cached
            
        _log.debug('Data cache miss for {:s}; retrieving from scryfall...'.format(cachepath))

        candidates = self.search_cards(name, exact=True, set_code=set_code)
        num = candidates[0].number
        self._cache.set(cachepath, num)
        self._save_cache()
        return num

    def get_card_back_image(self) -> Tuple[bytes, str]:
        """
        Get the back image for a card, from cache or from the defined URI if cache
        is not present.

        Returns a tuple of the image bytes and the format extension, such as
        'png', 'jpg', etc.
        """
        fmt = _BACK_IMAGE_URI.rsplit('.', 1)[1]

        cachepath = '/images/misc/back.' + fmt
        data, hit = self._filestore.get(cachepath)
        if hit:
            return data[0], fmt

        _log.debug('Image cache miss for {:s}; retrieving from scryfall...'.format(cachepath))

        image_data = http.download(_BACK_IMAGE_URI)

        self._filestore.set(cachepath, image_data)
        self._save_cache()

        return image_data, fmt


    def get_card_image(
        self,
        set_code: str, number: str, lang: str=None,
        size: card.Size=card.SizeFull, back: bool=False
    ) -> bytes:
        """Get image on a card by its collector's number within a set. If lang
        is given, card in that language is retrieved instead of the english one.
        
        Size can be specified. It can be either SizeFull, SizeSmall, SizeNormal,
        or SizeLarge, and defaults to SizeFull.

        Returns image bytes in the format specified by the size. Calling at
        least once ensures it is created and locally cached for future calls.
        
        Raises APIError if there is an issue with the request.
        """
        if isinstance(size, str):
            size = card.size_from_str(size)
        
        set_code = set_code.lower()
        cachelang = lang if lang is not None else 'en'
        frontback = 'back' if back else 'front'

        num_padded = number
        try:
            only_int = int(number, 10)
            num_padded = '{:03d}'.format(only_int)
        except TypeError:
            pass

        cachepath = '/images/set-{0:s}/card-{1:s}/{0:s}-{1:s}-{2:s}-{3:s}-{4:s}.{5:s}'.format(set_code, num_padded, frontback, size.name, cachelang, size.format)

        file_data, exists = self._filestore.get(cachepath)
        if exists:
            return file_data[0]
        
        _log.debug('Image cache miss for {:s}; retrieving from scryfall...'.format(cachepath))

        # otherwise, need to make the scryfall call
        lang_url = '/' + lang if lang is not None else ''
        path = '/cards/{:s}/{:s}{:s}'.format(set_code, number, lang_url)
        params = {
            'version': size.api_name,
            'format': 'image'
        }
        if back:
            params['face'] = 'back'
        
        status, resp = self._http.request('GET', path, query=params, response_payload='binary')
        if status >= 400:
            err = APIError.parse(resp)
            raise err
        
        self._filestore.set(cachepath, resp)
        self._save_cache()
        return resp

    def get_set(self, code: str) -> mtgset.Set:
        """
        Get details on a set by its set code.
        
        Raises APIError if there is an issue with the request.
        """
        code = code.lower()

        # check cache first
        cachepath = '/sets/{:s}/info'.format(code)
        cached, hit = self._cache.get(cachepath)
        if hit:
            return mtgset.Set(**cached)

        _log.debug('Data cache miss for {:s}; retrieving from scryfall...'.format(cachepath))
        
        params = {
            'pretty': self._pretty_response
        }

        status, resp = self._http.request('GET', '/sets/{:s}'.format(code), query=params)
        if status >= 400:
            err = APIError.parse(resp)
            raise err

        # set up properties for Set obj
        resp['type'] = resp['set_type']
        if 'released_at' in resp:
            rd = dateutil.parser.parse(resp['released_at'])
            if rd.tzinfo is None:
                rd = rd.replace(tzinfo=dateutil.tz.gettz('America/Los_Angeles'))
            resp['release_date'] = rd

        s = mtgset.Set(**resp)
        self._cache.set(cachepath, s.to_dict())
        self._save_cache()
        return s
        
    def _save_cache(self):
        try:
            with open(self._cachefile, 'wb') as fp:
                pickle.dump({
                    'requests': self._cache.store,
                    'files': self._filestore.store
                }, fp)
        except:
            _log.warn("couldn't load cache file; a new cache will be started")


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
    if layout.lower() in ['split', 'flip', 'transform', 'double_faced_token', 'modal_dfc']:
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
