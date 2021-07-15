from typing import Optional
from . import http

class ScryfallAgent:
    def __init__(self, host: str, pretty: bool=False):
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

    def get_card_by_name(self,
            name: str, fuzzy: bool=False, set_code: Optional[str] = None
    ):
        """Get details on a card by name. If fuzzy, fuzzy search is applied. If
        set_code is given, it is a three-letter set code that the lookup will
        be limited to."""
        params = {
            'pretty': self._pretty_response
        }
        if fuzzy:
            params['fuzzy'] = name
        else:
            params['exact'] = name
        _, resp = self._http.request('GET', '/cards/named', query=params)
        return resp
        