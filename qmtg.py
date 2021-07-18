from quickmtg.actions import search_cards, show_card, get_card_image
from quickmtg import scryfall
import sys
import pprint
import logging
import logging.handlers
import argparse


_log = logging.getLogger('qmtg')
_log.setLevel(logging.DEBUG)


def main():
    _setup_console_logger()

    # noinspection PyBroadException
    try:
        _parse_cli_and_run()
    except Exception:
        _log.exception("Problem during execution")
        sys.exit(1)
    sys.exit(0)

def _parse_cli_and_run():
    api = scryfall.ScryfallAgent('api.scryfall.com', pretty=True)
    
    parser = argparse.ArgumentParser(description="MTG library organizer")

    # space at the end of metavar is not a typo; we need it so help output is prettier
    subparsers = parser.add_subparsers(description="Functionality to execute.", metavar=" SUBCOMMAND ", dest='cmd')
    subparsers.required = True

    # Card actions
    card_parser = subparsers.add_parser('card', help='Perform an action against the card API.', description="Card lookup actions.")
    card_subs = card_parser.add_subparsers(description="Action on card(s)", metavar="ACTION", dest='cmdaction')
    card_subs.required = True

    # Card search
    card_search_parser = card_subs.add_parser('search', help='Search for a card by matching against the name. The most recent card to be released that matches will be returned.', description="Search for a card by name.")
    card_search_parser.add_argument('names', help="The name(s) of the card(s) to search for.", nargs='+', metavar='CARD')
    card_search_parser.add_argument('-f', '--fuzzy', help="Do a fuzzy search instead of exact name match.", action='store_true')
    card_search_parser.add_argument('-s', '--set', help="Limit the lookup to a particular set denoted by the three to five-letter set-code.", action='store')
    card_search_parser.set_defaults(func=lambda ns: search_cards(api, ns.fuzzy, ns.set, *ns.names))

    # Card look up
    card_search_parser = card_subs.add_parser('show', help='Look up a particular card by using its set ID and collector number within that set.', description="Look up a card by its number.")
    card_search_parser.add_argument('set', help="The three or to five-letter code that represents the set the card is in")
    card_search_parser.add_argument('num', help="The collector number of the card within the set.", type=int)
    card_search_parser.add_argument('-l', '--lang', help="The 2-3 letter language code of the language to get details of the card in, if non-english is desired.")
    card_search_parser.set_defaults(func=lambda ns: show_card(api, ns.set, ns.num, ns.lang))

    card_image_parser = card_subs.add_parser('image', help="Ensure that a card's image is downloaded.")
    card_image_parser.add_argument('set', help="The three or to five-letter code that represents the set the card is in")
    card_image_parser.add_argument('num', help="The collector number of the card within the set.", type=int)
    card_image_parser.add_argument('size', help="The collector number of the card within the set.", choices=['full', 'large', 'normal', 'small'])
    card_image_parser.add_argument('-l', '--lang', help="The 2-3 letter language code of the language to get details of the card in, if non-english is desired.")
    card_image_parser.add_argument('-b', '--back', help="Get the back face instead of the front face, if there is one.", action='store_true')
    card_image_parser.set_defaults(func=lambda ns: get_card_image(api, ns.set, ns.num, ns.lang, ns.size, ns.back))
    
    args = parser.parse_args()
    args.func(args)


class _ExactLevelFilter(object):
    """
    Only allows log records through that are particular levels.
    """

    def __init__(self, levels):
        """
        Creates a new exact level filter.
        :type levels: ``list[int|str]``
        :param levels: The levels that should pass through the filter; all others are filtered out. Each item is either
        one of the predefined level names or an integer level.
        """
        self._levels = set()
        for lev in levels:
            is_int = False
            try:
                lev = lev.upper()
            except AttributeError:
                is_int = True
            if not is_int:
                if lev == 'DEBUG':
                    self._levels.add(logging.DEBUG)
                elif lev == 'INFO':
                    self._levels.add(logging.INFO)
                elif lev == 'WARNING' or lev == 'WARN':
                    self._levels.add(logging.WARNING)
                elif lev == 'ERROR':
                    self._levels.add(logging.ERROR)
                elif lev == 'CRITICAL':
                    self._levels.add(logging.CRITICAL)
                else:
                    raise ValueError("bad level name in levels list: " + lev)
            else:
                self._levels.add(int(lev))

    def num_levels(self):
        """
        Gets the number of levels that are allowed through the filter.
        :rtype: ``int``
        :return: The number of levels.
        """
        return len(self._levels)

    def min_level(self):
        """
        Gets the minimum level that is allowed through the filter.
        :rtype: ``int``
        :return: The minimum leel
        """
        return min(self._levels)

    def filter(self, record):
        """
        Check whether to include the given log record in the output.
        :type record: ``logging.LogRecord``
        :param record: The record to check.
        :rtype: ``int``
        :return: 0 indicates the log record should be discarded; non-zero indicates that the record should be
        logged.
        """
        if record.levelno in self._levels:
            return 1
        else:
            return 0


def _setup_console_logger():
    file_handler = logging.handlers.RotatingFileHandler('qmtg.log', maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)

    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger().addHandler(stderr_handler)

    lev_filter = _ExactLevelFilter(['INFO'])
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(lev_filter.min_level())
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    stdout_handler.addFilter(lev_filter)
    logging.getLogger().addHandler(stdout_handler)
    


if __name__ == '__main__':
    main()
