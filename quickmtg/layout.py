
import math
from quickmtg.card import SizeSmall, image_slug
from typing import Any, Callable, Dict, Iterable, Optional, Sequence

"""gen_x functions end in newline, make_x funcs do not"""

class Indenter:
    """
    Does indenting.
    
    Calling str() on indenter returns the indent.
    """

    def __init__(self, indent: str='  ', level: int=0):
        self.level = level
        self.indent = indent

    def at(self, level: int) -> 'Indenter':
        """
        Return a new indenter that does indenting at the same level as this one
        with the given adjustment. Example: if at(1) is called on an indenter
        with level 4, it returns an indenter at level 5.

        Negative numbers can be given to return an Indenter with *less* of an
        indent than the current one.
        
        If the sum of the current level and the level adjustment is less than 0,
        it is clamped at 0.
        """

        new_lev = self.level + level
        if new_lev < 0:
            new_lev = 0
        return Indenter(self.indent, new_lev)


    def make(self, extra_levels: int=0) -> str:
        return self.indent * (self.level + extra_levels)

    def __call__(self, extra_levels: int=0) -> str:
        return self.make(extra_levels)

    def __str__(self) -> str:
        return self.make()

def gen_index_page(indent: Optional[Indenter]=None):
    if indent is None:
        indent = Indenter()

    content = ''
    content += indent(0) + '<!DOCTYPE html>\n'
    content += indent(0) + '<html>\n'
    content += indent(1) + '<head>\n'
    content += indent(2) + '<title>Index</title>\n'
    content += indent(1) + '</head>\n'
    content += indent(1) + '<body>\n'
    content += indent(2) + '<h1>Binder Index</h1>\n'
    content += indent(2) + '<a href="binder001.html">First Page</a>\n'
    content += indent(1) + '</body>\n'
    content += indent(0) + '</html>\n'

    return content


def gen_binder_page(cards: Sequence[Dict[str, Any]], pageno: int, rows: int, cols: int, indent: Optional[Indenter]=None):
    if indent is None:
        indent = Indenter()
    
    cards_on_page = rows * cols
    total_pages = int(math.ceil(len(cards) / cards_on_page))
    
    content = ''
    content += indent(0) + '<!DOCTYPE html>\n'
    content += indent(0) + '<html>\n'
    content += indent(1) + '<head>\n'
    content += indent(2) + '<title>Binder Page {:d}</title>\n'.format(pageno)
    content += indent(1) + '</head>\n'
    content += indent(1) + '<body>\n'
    content += indent(2) + '<div class="title">\n'
    content += indent(3) + '<h1>Binder</h1>\n'
    content += indent(3) + '<h2>Page {:d}/{:d}</h2>\n'.format(pageno, total_pages)
    content += indent(2) + '</div>\n'

    content += gen_binder_nav(pageno, total_pages, indent.at(2))
    content += gen_binder_table(cards, rows, cols, indent.at(2))
    content += gen_binder_nav(pageno, total_pages, indent.at(2))
    
    content += indent(1) + '</body>\n'
    content += indent(0) + '</html>\n'
    return content

def gen_binder_table(cards: Sequence[Dict[str, Any]], rows: int, cols: int, indent: Optional[Indenter]=None):
    if indent is None:
        indent = Indenter()
    
    content = ''
    content += indent(0) + '<table class="binderpage">\n'

    for y in range(rows):
        content += indent(1) + '<tr>\n'

        for x in range(cols):
            idx = y*cols + x
            c = cards[idx]
            content += indent(2) + make_card_cell(c) + '\n'

        content += indent(1) + '</tr>\n'
    
    content += indent(0) + '</table>\n'
    return content

def gen_binder_nav(pageno: int, total_pages: int, indent: Optional[Indenter]=None):
    if indent is None:
        indent = Indenter()

    prev_file = None
    if pageno > 1:
        prev_file = 'binder{:03d}.html'.format(pageno - 1)
    next_file = None
    if pageno + 1 < total_pages:
        next_file = 'binder{:03d}.html'.format(pageno + 1)

    content = ''
    content += indent(0) + '<nav class="binder">\n'

    if prev_file is None:
        content += indent(1) + '<a class="disabled" href="#">&larr;</a>\n'
    else:
        content += indent(1) + '<a href="{:s}">&larr;</a>\n'.format(prev_file)

    content += indent(1) + '<a href="index.html">Index</a>\n'

    if next_file is None:
        content += indent(1) + '<a class="disabled" href="#">&rarr;</a>\n'
    else:
        content += indent(1) + '<a href="{:s}">&rarr;</a>\n'.format(next_file)

    content += indent(0) + '</nav>\n'
    return content

def make_card_cell(card_data: Optional[Dict[str, Any]], indent: Optional[Indenter]=None):
    if indent is None:
        indent = Indenter()
    
    if card_data is None:
        return indent(0) + '<td class="empty"><img src="assets/images/back.png" alt="a blank slot" /></td>'
    else:
        owned_card = card_data['card']
        s = indent(0) + '<td class="filled'
        if owned_card.foil:
            s += ' foil'
        s += '">'
        # TODO: add num owned as overlay in future
        s += '<img src="assets/images/' + image_slug(owned_card, SizeSmall)
        s += '" width="{:d}" height="{:d}" alt="{:s}"/>'.format(SizeSmall.w, SizeSmall.h, owned_card.setnum)
        s += '</td>'
        return s