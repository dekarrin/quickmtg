from enum import Enum
from typing import Dict, FrozenSet, Iterable, Optional, Sequence, Set, Tuple

class Color:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol

    def __repr__(self) -> str:
        return 'Color({!r}, {!r})'.format(self.name, self.symbol)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Color):
            return NotImplemented
        
        if not self.name == other.name:
            return False
        elif not self.symbol == other.symbol:
            return False
        return True

    def __lt__(self, other):
        if not isinstance(other, Color):
            return NotImplemented

        return self._order_num() < other._order_num()

    def __ne__(self, other):
        if not isinstance(other, Color):
            return NotImplemented
        return not self.__eq__(other)

    def __le__(self, other):
        if not isinstance(other, Color):
            return NotImplemented

        return self.__eq__(other) or self.__lt__(other)

    def __gt__(self, other):
        if not isinstance(other, Color):
            return NotImplemented
        return not self.__le__(other)

    def __ge__(self, other):
        if not isinstance(other, Color):
            return NotImplemented
        return not self.__lt__(other)

    def __hash__(self):
        return hash((self.name, self.symbol,))

    def _order_num(self) -> int:
        order = ['W', 'U', 'B', 'R', 'G', '']
        if self.symbol not in order:
            return len(order)
        return order.index(self.symbol)

WHITE = Color('WHITE', 'W')
BLUE = Color('BLUE', 'U')
BLACK = Color('BLACK', 'B')
RED = Color('RED', 'R')
GREEN = Color('GREEN', 'G')
COLORLESS = Color('COLORLESS', '')

AnyColor: FrozenSet[Color] = frozenset(WHITE, BLUE, BLACK, RED, GREEN,)
AnyMana: FrozenSet[Color] = frozenset(WHITE, BLUE, BLACK, RED, GREEN, COLORLESS,)

class Payable:
    """
    Represents a 'cost' that can be paid using particular means, usually mana.
    
    Other costs are possible, for example phyrexian mana can be paid by paying
    life, and snow requires any mana produced by a snow-source."""
    def __init__(self, amount: float, *mana_colors: Color, special: Optional[str]=None, dual_generic: Optional[int]=None):
        """
        Create a new Payable.
        
        :param amount: The amount that must be paid. Note that this can be
        infinity.
        :param mana_colors: The color(s) of mana that can be used to satisfy the
        cost specified by this Payable. If none are provided, a specialized
        non-mana cost is assumed (as is the case with acorn counters), and
        `special` must be specified to give the special kind of thing that is
        required to be paid (in the case with acorns, it would be set to
        'acorn').
        :param special: The special feature or variation of the payable. Setting
        this indicates that either the mana used to pay it must have a special
        feature (as with snow costs), or that alternatives to mana may be used
        to satisfy the payable (as with phyrexian mana costs), or MUST be used
        to satisfy the payable (as with acorn costs).
        :param dual_generic: If set to an integer, the cost may be fullfilled by
        paying dual_generic mana of any type in addition to the other specified
        cost.
        """

        # make sure we arent being passed in a bunk cost, Payable instances need
        # to know what fills them at construction time
        if len(mana_colors) == 0:
            if special is None or str(special) == '':
                raise ValueError("no mana color(s) given for Payable, so param 'special' cannot be empty")

        self.special: str = ''
        self.amount: int = int(amount)
        self.colors: FrozenSet[Color] = frozenset()
        self.dual_generic: Optional[int] = dual_generic

        mana_set = set()
        for x in mana_colors:
            if isinstance(x, frozenset) or isinstance(x, set):
                mana_set.update(x)
            else:
                mana_set.add(x)
        self.colors: FrozenSet[Color] = frozenset(mana_set)


        if special is not None:
            self.special = str(special)

    @property
    def cmc(self) -> int:
        if self.dual_generic is not None:
            return self.dual_generic
        else:
            return self.amount

    @property
    def phyrexian(self) -> bool:
        return self.special == 'phyrexian'

    @property
    def snow(self) -> bool:
        return self.special == 'snow'
        
    @property
    def acorn(self) -> bool:
        return self.special == 'acorn'

    def _id_tuple(self) -> Tuple:
        return (self.amount, self.colors, self.special, self.dual_generic)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return self._id_tuple() == other._id_tuple()

    def __ne__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return self._id_tuple() < other._id_tuple()

    def __le__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return not self.__le__(other)

    def __ge__(self, other) -> bool:
        if not isinstance(other, Payable):
            return NotImplemented
        return not self.__lt__(other)

    def __hash__(self) -> int:
        return hash(self._id_tuple())

    def __str__(self) -> str:
        s = 'Pay {:d}'.format(self.amount)
        if self.colors != AnyMana:
            if self.colors == AnyColor:
                s += ' mana of any color'
            elif len(self.colors) > 0:
                for x in self.colors:
                    s += x.name + ', or '
                s = s[:-5]
        if self.special == 'phyrexian':
            s += ' or 2 life'
        elif self.special == 'snow':
            s += ' (snow)'
        elif self.special == 'acorn':
            s += ' acorn counter(s)'
        if self.dual_generic is not None:
            s += ' or {:d} mana of any color'.format(self.dual_generic)
        return s

    def __repr__(self) -> str:
        s = 'Payable({!r}, {!r}, special={!r}, dual_generic={!r})'
        return s.format(self.amount, self.colors, self.special, self.dual_generic)


def cost_to_cmc(cost: str) -> int:
    cmc = 0
    cur_sym_partial = ''
    in_symbol = False
    for c in cost:
        if in_symbol:
            if c == '}':
                in_symbol = False
                p = _symbol_to_cmc(cur_sym_partial)
                cur_sym_partial = ''
                cmc += p.cmc
            else:
                cur_sym_partial += c
        elif c == '{':
            in_symbol = True
    return cmc


def _symbol_to_cmc(cost_sym: str) -> Payable:
    """
    Return (payable, amount) for a symbol string, giving the amount that needs
    to be paid as well as the set of colors of mana that can be used to pay it.

    If the cost is in generic mana, the payable set will be filled with all
    colors of mana as well as the special constant COLORLESS, since any type of
    mana may be used to pay it. If the cost requires colored mana to be paid (as
    is the case with non-colored phyrexian mana symbols), the payable set will
    include all colors of mana but will not include COLORLESS.
    """
    cost_sym = cost_sym.upper()

    # this parse doesn't check for slashes in any except for one case, so that
    # the parse does not depend on the order of checks

    if cost_sym.startswith('H') and len(cost_sym) == 2:
        try:
            pay = _symbol_to_cmc(cost_sym[1:2])
        except TypeError:
            raise TypeError("Unknown half-cost mana: {!r}".format(cost_sym))
        else:
            return Payable(0.5, *pay.colors)
    if cost_sym == '∞':
        return Payable(float('inf'), AnyMana)
    elif cost_sym == 'C':
        return Payable(1.0, COLORLESS)
    elif cost_sym == 'S':
        # snow land
        return Payable(1.0, AnyMana, special='snow')
    elif cost_sym == 'P' or cost_sym == 'Φ':
        # scryfall and standardized sources should never send and actual Φ
        # symbol as standard for phyrexian is 'P' but handle it just in case
        return Payable(1.0, AnyColor, special='phyrexian')
    elif cost_sym == '½':
        return Payable(0.5, AnyMana)
    elif cost_sym == 'X' or cost_sym == 'Y' or cost_sym == 'X':
        return Payable(0.0, AnyMana)
    elif cost_sym == 'W':
        return Payable(1.0, WHITE)
    elif cost_sym == 'U':
        return Payable(1.0, BLUE)
    elif cost_sym == 'B':
        return Payable(1.0, BLACK)
    elif cost_sym == 'R':
        return Payable(1.0, RED)
    elif cost_sym == 'G':
        return Payable(1.0, GREEN)
    elif '/' in cost_sym and len(cost_sym) == 3:
        halves = cost_sym.split('/', 1)
        if len(halves) != 2:
            raise TypeError("Unknown mana symbol: {!r}".format(cost_sym))
        
        left, right = halves[0], halves[1]
        left_payable = _symbol_to_cmc(left)
        right_payable = _symbol_to_cmc(right)
        if left_payable.phyrexian:
            return Payable(right_payable.amount, right_payable.colors, special='phyrexian')
        elif right_payable.phyrexian:
            return Payable(left_payable.amount, left_payable.colors, special='phyrexian')
        elif left_payable.colors == AnyMana:
            return Payable(1.0, right_payable.colors, dual_generic=left_payable.amount)
        elif right_payable.colors == AnyMana:
            return Payable(1.0, left_payable.colors, dual_generic=right_payable.amount)
        else:
            # it must be a dual color
            return Payable(1.0, left_payable.colors + right_payable.colors)
    else:
        try:
            cmc = float(cost_sym)
        except TypeError:
            raise TypeError("Unknown mana symbol: {!r}".format(cost_sym))
        else:
            return Payable(cmc, AnyMana)


def cost_contains(cost: str, c: Color) -> bool:
    if '{' + c.symbol + '}' in cost:
        return True
    if '{' + c.symbol + '/' in cost:
        return True
    if '/' + c.symbol + '}' in cost:
        return True
    return False


def extract_loyalty(cost: str) -> Set[Color]:
    s = set()
    if cost_contains(cost, WHITE):
        s.add(WHITE)
    if cost_contains(cost, BLUE):
        s.add(BLUE)
    if cost_contains(cost, BLACK):
        s.add(BLACK)
    if cost_contains(cost, RED):
        s.add(RED)
    if cost_contains(cost, GREEN):
        s.add(GREEN)
    return s

