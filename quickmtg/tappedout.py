from typing import Tuple
from . import card
from .card import OwnedCard, Card

import html

def parse_list_line(line: str) -> Tuple[int, OwnedCard]:
    """Parse a line from tapped out board format to owned number and card."""
    raw_count, rest = line.split(' ', 1)
    count = int(raw_count.strip('x'))
    c = parse_card_line(rest)
    return count, c

def to_list_line(owned: int, c: OwnedCard) -> str:
    return '{:d}x {:s}'.format(owned, to_list_line(c))

def parse_card_id(line: str) -> Card:
    """
    Return a card that has only name, set, and number set.
    """
    encoded_name, raw_set_id = line.rsplit(' ', 1)
    name = html.unescape(encoded_name)

    # remove '(' and ')'
    raw_set_id = raw_set_id[1:-1]
    num = 0
    if ':' in raw_set_id:
        set_code, raw_num = raw_set_id.split(':')
        num = int(raw_num)
    else:
        set_code = raw_set_id

    c = Card(name=name, set=set_code, number=num)
    return c

def to_card_id(c: Card) -> str:
    fmt = '{:s} ({:s}:{:03d})'
    return fmt.format(c.faces[0].name, c.set, c.number)

def parse_card_line(line: str) -> OwnedCard:
    foil = False
    cond = 'mint'
    curline = line
    curline, end = curline.rsplit(' ', 1)
    while end.startswith('*') and end.endswith('*'):
        if end == '*F*':
            foil = True
        else:
            cond = card.cond_from_symbol(end)    
        curline, end = curline.rsplit(' ', 1)
    c_args = parse_card_id(curline).to_dict()
    c = OwnedCard(condition=cond, foil=foil, **c_args)
    return c

def to_card_line(c: OwnedCard) -> str:
    line = to_card_id(c)
    if c.foil:
        line += ' *F*'
    if c.condition != card.MINT:
        line += ' *' + c.condition.symbol + '*'
    return line
