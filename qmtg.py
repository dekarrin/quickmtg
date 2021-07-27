from quickmtg.actions import delete_view, edit_view, search_cards, show_card, get_card_image, create_view, list_views, show_view
from quickmtg import scryfall, storage
import sys
import pprint
import logging
import logging.handlers
import argparse
import os.path


_log = logging.getLogger('qmtg')
_log.setLevel(logging.DEBUG)


def main():
    _setup_console_logger()

    # noinspection PyBroadException
    try:
        _parse_cli_and_run()
    except KeyboardInterrupt:
        pass
    except Exception:
        _log.exception("Problem during execution")
        sys.exit(1)
    sys.exit(0)

def _parse_cli_and_run():
    api: scryfall.ScryfallAgent = None
    store: storage.AutoSaveStore = None
    default_home_path = os.path.join(os.path.expanduser("~"), '.qmtg')
    
    parser = argparse.ArgumentParser(description="MTG library organizer")
    parser.add_argument('-m', '--qmtg-home', help='Where to store persistence data and locations of binders.', default=default_home_path)

    # space at the end of metavar is not a typo; we need it so help output is prettier
    subparsers = parser.add_subparsers(description="Functionality to execute.", metavar=" SUBCOMMAND ", dest='cmd')
    subparsers.required = True

    # View actions
    view_parser = subparsers.add_parser('view', help='Operates on binder views generated from tappedout.net card lists in board format.', description="HTML binder operations.")
    view_subs = view_parser.add_subparsers(description="Action on views", metavar="ACTION", dest='cmdaction')
    view_subs.required = True

    # View listing
    view_list_parser = view_subs.add_parser('list', help='List out the IDs of every binder view that exists on the system.', description='List all current binder views')
    view_list_parser.set_defaults(func=lambda ns: list_views(store, api))

    # View showing
    view_show_parser = view_subs.add_parser('show', help='Shows all information on a binder view, including name, path, and number of cards in the view.', description='Show info on a binder view')
    view_show_parser.add_argument('binder', help="The ID of the binder to show info on")
    view_show_parser.add_argument('-c', '--cards', help="Give a complete list of cards instead of just giving a count.", action='store_true')
    view_show_parser.set_defaults(func=lambda ns: show_view(store, ns.binder, ns.cards))

    # View deleting
    view_delete_parser = view_subs.add_parser('delete', help='Removes a binder view from QMTG tracking. If specified, also deletes the built binder view.', description='Remove a binder view')
    view_delete_parser.add_argument('binder', help="The ID of the binder to delete")
    view_delete_parser.add_argument('--delete-directory', help="Delete the entire built binder view files on disk in addition to removing the binder from tracking.", action='store_true')
    view_delete_parser.set_defaults(func=lambda ns: delete_view(store, ns.binder, ns.delete_directory))
    
    # View editing
    view_edit_parser = view_subs.add_parser('edit', help='Edits properties of a binder. This can be used to, for example, update QMTG tracking with the location of a moved view binder directory.', description='Edit properties of a binder view')
    view_edit_parser.add_argument('binder', help="The ID of the binder to edit")
    view_edit_parser.add_argument('--id', help="A new ID to set for the binder.")
    view_edit_parser.add_argument('-n', '--name', help="A new name to set for the binder.")
    view_edit_parser.add_argument('--path', help="A new directory path to set for the binder.")
    view_edit_parser.set_defaults(func=lambda ns: edit_view(store, ns.binder, ns.id, ns.name, ns.path))

    # View creation
    view_create_parser = view_subs.add_parser('create', help='Create a new binder view from the given owned cards list. HTML pages containing the binder are output to a directory, and an index.html is created as the starting point for viewing the binder.', description='Create a new binder view.')
    view_create_parser.add_argument('-n', '--name', help="what to call the binder view")
    view_create_parser.add_argument('--id', help="An ID to internally call the binder")
    view_create_parser.add_argument('input_list', help='The file to parse for the cards in it. Must contain a list in tappedout.net board format text, which is known to sometimes be not perfect.')
    view_create_parser.add_argument('output_dir', help="The directory to store the output files in. Will be created if it doesn't already exist.")
    view_create_parser.set_defaults(func=lambda ns: create_view(store, api, ns.input_list, ns.output_dir, name=ns.name, id=ns.id))

    # Card actions
    card_parser = subparsers.add_parser('card', help='Perform an action against the card API.', description="Card lookup actions.")
    card_subs = card_parser.add_subparsers(description="Action on card(s)", metavar="ACTION", dest='cmdaction')
    card_subs.required = True

    # Card search - NOTE: uses /cards/named endpoint, NOT /cards/search. Update to use later at some point
    card_search_parser = card_subs.add_parser('search', help='Search for a card by matching against the name. The most recent card to be released that matches will be returned.', description="Search for a card by name.")
    card_search_parser.add_argument('names', help="The name(s) of the card(s) to search for.", nargs='+', metavar='CARD')
    card_search_parser.add_argument('-f', '--fuzzy', help="Do a fuzzy search instead of exact name match.", action='store_true')
    card_search_parser.add_argument('-s', '--set', help="Limit the lookup to a particular set denoted by the three to five-letter set-code.", action='store')
    card_search_parser.set_defaults(func=lambda ns: search_cards(api, ns.fuzzy, ns.set, *ns.names))

    # Card look up
    card_search_parser = card_subs.add_parser('show', help='Look up a particular card by using its set ID and collector number within that set.', description="Look up a card by its number.")
    card_search_parser.add_argument('set', help="The three or to five-letter code that represents the set the card is in")
    card_search_parser.add_argument('num', help="The collector number of the card within the set.")
    card_search_parser.add_argument('-l', '--lang', help="The 2-3 letter language code of the language to get details of the card in, if non-english is desired.")
    card_search_parser.set_defaults(func=lambda ns: show_card(api, ns.set, ns.num, ns.lang))

    card_image_parser = card_subs.add_parser('image', help="Ensure that a card's image is downloaded.")
    card_image_parser.add_argument('set', help="The three or to five-letter code that represents the set the card is in")
    card_image_parser.add_argument('num', help="The collector number of the card within the set.")
    card_image_parser.add_argument('size', help="The collector number of the card within the set.", choices=['full', 'large', 'normal', 'small'])
    card_image_parser.add_argument('-l', '--lang', help="The 2-3 letter language code of the language to get details of the card in, if non-english is desired.")
    card_image_parser.add_argument('-b', '--back', help="Get the back face instead of the front face, if there is one.", action='store_true')
    card_image_parser.set_defaults(func=lambda ns: get_card_image(api, ns.set, ns.num, ns.lang, ns.size, ns.back))
    
    args = parser.parse_args()

    try:
        os.mkdir(args.qmtg_home, 0o770)
    except FileExistsError:
        pass
        # thats okay we just need it to exist

    cachepath = os.path.join(args.qmtg_home, 'scryfall.p')
    filepath = os.path.join(args.qmtg_home, 'filestore')
    api = scryfall.ScryfallAgent('api.scryfall.com', pretty=False, cachefile=cachepath, file_home=filepath)
    store = storage.AutoSaveStore(os.path.join(args.qmtg_home, 'qmtp.p'))
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
    file_handler = logging.handlers.RotatingFileHandler('qmtg.log', maxBytes=25*1024*1024, backupCount=5)
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
