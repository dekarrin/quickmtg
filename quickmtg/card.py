from . import color
from .color import Color
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import logging


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class Size:
    def __init__(self, name: str, api_name: str, w: int, h: int, file_format: str):
        self.name = name
        self.api_name = api_name
        self.format = file_format
        self.width = w
        self.height = h
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Size({!r}, {!r}, {!r}, {!r}, {!r})'.format(
            self.name,
            self.api_name,
            self.w,
            self.h,
            self.format
        )

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def w(self) -> int:
        return self.width

    @property
    def h(self) -> int:
        return self.height

SizeFull = Size('full', 'png', 745, 1040, 'png')
SizeLarge = Size('large', 'large', 672, 936, 'jpg')
SizeNormal = Size('normal', 'normal', 488, 680, 'jpg')
SizeSmall = Size('large', 'large', 146, 204, 'jpg')

def size_from_str(s: str) -> Size:
    if s.lower() not in ['full', 'small', 'normal', 'large']:
        err = "Invalid size for card"
        err += "; must be one of 'full', 'small', 'normal', or 'large'"
        err += " but was: {!r}".format(s)
        raise TypeError(err)
    
    if s.lower() == 'full':
        return SizeFull
    elif s.lower() == 'large':
        return SizeLarge
    elif s.lower() == 'normal':
        return SizeNormal
    elif s.lower() == 'small':
        return SizeSmall

    # should never happen due to prechecks but check anyways
    raise TypeError("Not a valid size string: {!r}".format(s))


class Condition:
    def __init__(self, name: str, symbol: str, id: int):
        self.name = name
        self.symbol = symbol
        self.id = id

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.symbol

    def __eq__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented
        
        return self.id == other.id

    def __ne__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented
        
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented
        
        return self.id < other.id
    
    def __le__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented
        
        return self < other or self == other

    def __gt__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented

        return not (self <= other)

    def __ge__(self, other):
        if not isinstance(other, Condition):
            return NotImplemented

    def __hash__(self):
        return hash((self.name, self.symbol,))

MINT = Condition('MINT/NEAR MINT', '', 0)
SLIGHTLY_USED = Condition('SLIGHTLY USED', 'SL', 1)
MEDIUM_USED = Condition('MEDIUM USED', 'ME', 2)
HEAVY_USED = Condition('HEAVY USED', 'HE', 3)


def cond_from_symbol(symbol: str) -> Condition:
    """Return the condition represented by the given symbol. Returns MINT if
    none found."""
    symbol = symbol.strip('*')
    if symbol == SLIGHTLY_USED.symbol:
        return SLIGHTLY_USED
    if symbol == MEDIUM_USED.symbol:
        return MEDIUM_USED
    if symbol == HEAVY_USED.symbol:
        return HEAVY_USED
    return MINT


class Face:
    def __init__(self, **kwargs):
        self.name = ''
        self.type = ''
        self.cost = ''
        self.text = ''
        self.power: Optional[str] = None
        self.toughness: Optional[str] = None

        if kwargs is not None:
            if 'name' in kwargs:
                self.name = kwargs['name']
            if 'type' in kwargs:
                self.type = kwargs['type']
            if 'cost' in kwargs:
                self.cost = kwargs['cost']
            if 'text' in kwargs:
                self.text = kwargs['text']
            if 'toughness' in kwargs:
                self.toughness = kwargs['toughness']
            if 'power' in kwargs:
                self.power = kwargs['power']

    def __eq__(self, other) -> bool:
        if not isinstance(other, Face):
            return False
        else:
            return self._id_tuple() == other._id_tuple()

    def __hash__(self) -> int:
        return hash(self._id_tuple())

    def __str__(self) -> str:
        s = 'Face<{!r} cost={!r} type={!r}'.format(self.name, self.cost, self.type)
        if self.text is None or self.text == '':
            s += ' text=(none)'
        else:
            s += ' text={!r}'.format(self.text)
        
        if self.power is not None and self.power != '':
            s += ' s/t=\"' + self.power + '/'
            if self.toughness is not None and self.toughness != '':
                s += self.toughness
            s += '"'

        return s

    def __repr__(self) -> str:
        fmt = 'Face(name={!r}, cost={!r}, type={!r}, text={!r}, power={!r}, toughness={!r})'
        return fmt.format(self.name, self.cost, self.type, self.text, self.power, self.toughness)

    def _id_tuple(self) -> Tuple:
        return (
            self.name,
            self.type,
            self.cost,
            self.text,
            self.toughness,
            self.power
        )

    @property
    def color_loyalty(self) -> Set[Color]:
        s = color.extract_loyalty(self.cost)
        s.update(color.extract_loyalty(self.text))
        return s

    @property
    def color(self) -> Set[Color]:
        return color.extract_loyalty(self.cost)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'cost': self.cost,
            'text': self.text,
            'power': self.power,
            'toughness': self.toughness
        }


class Card:
    def __init__(self, **kwargs):
        self.id: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
        self.set: str = ''
        self.language: str = 'en'
        self.rarity: str = ''
        self.faces: List[Face] = list()
        self.number = None
        self.active_face: int = 0

        if kwargs is not None:
            if 'id' in kwargs:
                id = kwargs['id']
                if isinstance(id, uuid.UUID):
                    self.id = id
                else:
                    self.id = uuid.UUID(kwargs['id'])
            if 'set' in kwargs:
                self.set = kwargs['set']
            if 'rarity' in kwargs:
                self.rarity = kwargs['rarity']
            if 'faces' in kwargs:
                self.faces = list((f if isinstance(f, Face) else Face(**f)) for f in kwargs['faces'])
            if 'number' in kwargs:
                self.number = kwargs['number']
            if 'language' in kwargs:
                self.language = kwargs['language']
            if 'active_face' in kwargs:
                self.active_face = int(kwargs['active_face'])

    @property
    def pretty_num(self) -> str:
        if self.number == '':
            return ''
        try:
            i = int(self.number, 10)
            return '{:03d}'.format(i)
        except TypeError:
            pass

        return self.number

    @property
    def number(self) -> str:
        if self._num is None:
            return ''
        return self._num

    @number.setter
    def number(self, v: Union[str, int]):
        if v is None:
            self._num = v
            return
        
        if isinstance(v, int):
            v = str(v)

        # chop off leading 0's
        while v.startswith('0'):
            v = v[1:]
        
        self._num = v
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        else:
            if self.id != other.id:
                return False
            if self.set != other.set:
                return False
            if self.rarity != other.rarity:
                return False
            if self.number != other.number:
                return False
            if self.language != other.language:
                return False
            if len(self.faces) != len(other.faces):
                return False
            for f, other_f in zip(self.faces, other.faces):
                if f != other_f:
                    return False

            return True

    def __ne__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            raise NotImplemented()
        
        self_props = self._order_index()
        other_props = other._order_index()

        return self_props < other_props

    def _order_index(self) -> Tuple:
        return (
            self._type_order_index(),
            self._color_order_index(),
            self.cmc,
            self.power if self.power else '',
            self.toughness if self.toughness else '',
            self.name,
        )

    def __le__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return not self.__lt__(other)

    def __gt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return not self.__le__(other)
    
    def __hash__(self) -> int:
        return hash((self.id, self.set, self.rarity, self.number, self.language, frozenset(self.faces), self.active_face))

    def __str__(self) -> str:
        return 'Card<{:s} {!r}>'.format(self.setnum, self.name)

    def __repr__(self) -> str:
        fmt = 'Card(id={!r}, set={!r}, number={!r}, rarity={!r}, faces={!r})'
        return fmt.format(self.id, self.set, self.number, self.rarity, self.faces)

    def _color_order_index(self) -> int:
        if len(self.color) == 0:
            return 5  # if no color, come last
        c_order: int = 0
        if color.WHITE in self.color:
            c_order = 0
        elif color.BLUE in self.color:
            c_order = 1
        elif color.BLACK in self.color:
            c_order = 2
        elif color.RED in self.color:
            c_order = 3
        elif color.GREEN in self.color:
            c_order = 4
        c_order += 5 * (len(self.color) - 1)
        return c_order

    def _type_order_index(self) -> int:
        supertypes, card_type, subtypes = self._parsed_type()
        print("{!r}, {!r}, {!r}".format(supertypes, card_type, subtypes))

        if card_type == 'creature':
            checked_supertypes = list(supertypes)
            
            # snow creature are basically just creature
            # with identifier, so dont sort based on that
            if 'snow' in checked_supertypes:
                checked_supertypes.remove('snow')

            if len(checked_supertypes) == 0:
                return 0
            elif len(checked_supertypes) == 1:
                if checked_supertypes[0] == 'artifact':
                    return 1
                elif checked_supertypes[0] == 'enchantment':
                    return 2
                elif checked_supertypes[0] == 'legendary':
                    return 3
        elif card_type == 'planeswalker':
            if len(supertypes) == 0:
               return 10
            elif len(supertypes) == 1:
                if supertypes[0] == 'legendary':
                    return 13
        elif card_type == 'land':
            checked_supertypes = list(supertypes)

            # snow lands shouldnt be sorted specially, nor should artifact lands
            if 'snow' in checked_supertypes:
                checked_supertypes.remove('snow')
            if 'artifact' in checked_supertypes:
                checked_supertypes.remove('artifact')

            if len(checked_supertypes) == 0:
               return 21
            elif len(checked_supertypes) == 1:
                if checked_supertypes[0] == 'basic':
                    return 20
        elif card_type == 'artifact':
            return 30
        elif card_type == 'enchantment':
            return 40
        elif card_type == 'sorcery':
            return 50
        elif card_type == 'instant':
            return 60
        raise ValueError('Not a parsable type_line: {!r}'.format(self.type))

    def _parsed_type(self) -> Tuple[List[str], str, List[str]]:
        subtypes = []
        card_type = ''
        supertypes = []
        halves = [s.strip().lower() for s in self.type.split('\u2014')]
        if len(halves) > 1:
            subtypes = halves[1].split(' ')
        types = halves[0].split(' ')
        if len(types) > 1:
            supertypes = types[:-1]
            card_type = types[-1]
        else:
            card_type = types[0]

        return supertypes, card_type, subtypes

    @property
    def has_other_side(self) -> bool:
        return len(self.faces) > 1

    @property
    def flipped(self) -> 'Card':
        """
        Return a Card with the active face to the next one up. If this card ha
        sonly one face, the returned card is identical.
        """
        d = self.to_dict()
        if len(self.faces) < 1:
            return Card(**d)
        face = self.active_face + 1
        face %= len(self.faces)
        d['active_face'] = face
        return Card(**d)

    @property
    def setnum(self) -> str:
        return '{:s}:{:s}'.format(self.set, self.pretty_num)

    @property
    def name(self) -> str:
        if len(self.faces) < self.active_face + 1:
            return ""
        return self.faces[self.active_face].name

    @property
    def all_names(self) -> str:
        if len(self.faces) < 1:
            return ""
        n = self.faces[0].name
        for face in self.faces[1:]:
            n += " // " + face.name
        return n

    @property
    def cmc(self) -> int:
        return color.cost_to_cmc(self.cost)

    @property
    def type(self) -> str:
        if len(self.faces) < self.active_face + 1:
            return ""
        return self.faces[self.active_face].type

    @property
    def all_types(self) -> str:
        if len(self.faces) < 1:
            return ""
        t = self.faces[0].type
        for face in self.faces[1:]:
            t += " // " + face.type
        return t

    @property
    def cost(self) -> str:
        if len(self.faces) < self.active_face + 1:
            return ""
        return self.faces[self.active_face].cost

    @property
    def all_costs(self) -> str:
        if len(self.faces) < 1:
            return ""
        c = self.faces[0].cost
        for face in self.faces[1:]:
            c += " // " + face.cost
        return c

    @property
    def text(self) -> str:
        if len(self.faces) < self.active_face + 1:
            return ""
        return self.faces[self.active_face].text

    @property
    def all_texts(self) -> str:
        if len(self.faces) < 1:
            return ""
        t = self.faces[0].text
        for face in self.faces[1:]:
            t += " // " + face.text
        return t

    @property
    def color_loyalty(self) -> Set[Color]:
        if len(self.faces) < 1:
            return set()
        s = self.faces[0].color_loyalty
        for face in self.faces[1:]:
            s.update(face.color_loyalty)
        return s

    @property
    def color(self) -> Set[Color]:
        if len(self.faces) < self.active_face + 1:
            return set()
        return self.faces[self.active_face].color

    @property
    def all_colors(self) -> Set[Color]:
        if len(self.faces) < 1:
            return set()
        s = set(self.faces[0].color)
        for face in self.faces[1:]:
            s.update(face.color)
        return s
        
    @property
    def power(self) -> Optional[str]:
        if len(self.faces) < self.active_face + 1:
            return None
        return self.faces[self.active_face].power

    @property
    def all_powers(self) -> List[Optional[str]]:
        if len(self.faces) < 1:
            return list()
        p = list(self.faces[0].power)
        for face in self.faces[1:]:
            p.append(face.power)
        return p
        
    @property
    def toughness(self) -> Optional[str]:
        if len(self.faces) < self.active_face + 1:
            return None
        return self.faces[self.active_face].toughness

    @property
    def all_toughnesses(self) -> List[Optional[str]]:
        if len(self.faces) < 1:
            return list()
        t = list(self.faces[0].toughness)
        for face in self.faces[1:]:
            t.append(face.toughness)
        return t
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'set': self.set,
            'rarity': self.rarity,
            'faces': [f.to_dict() for f in self.faces],
            'number': self.number,
            'language': self.language,
            'active_face': self.active_face
        }

class OwnedCard(Card):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.condition: Condition = None
        self.foil: bool = False
        self.count: int = 0

        if kwargs is not None:
            if 'condition' in kwargs:
                c = kwargs['condition']
                if isinstance(c, Condition):
                    self.condition = c
                else:
                    self.condition = cond_from_symbol(c)
            if 'foil' in kwargs:
                self.foil = kwargs['foil']
            if 'count' in kwargs:
                self.count = int(kwargs['count'])

    def __eq__(self, other) -> bool:
        if not isinstance(other, OwnedCard):
            return False
        elif not super().__eq__(other):
            return False
        elif self.condition != other.condition:
            return False
        elif self.foil != other.foil:
            return False
        elif self.count != other.count:
            return False
        return True

    def __ne__(self, other) -> bool:
        if not isinstance(other, OwnedCard):
            return NotImplemented
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, OwnedCard):
            raise NotImplemented()
        
        return self._order_index() < other._order_index()

    def __le__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return not self.__lt__(other)

    def __gt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return not self.__le__(other)

    def _order_index(self) -> Tuple:
        return (super()._order_index(), self.condition, self.foil, self.count,)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.condition, self.foil, self.count))

    def __str__(self) -> str:
        fstr = ''
        if self.foil:
            fstr = ' (FOIL)'
        return 'OwnedCard<{:s} {!r}{:s} x{:d}>'.format(self.setnum, self.name, fstr, self.count)

    def __repr__(self) -> str:
        fmt = 'OwnedCard(id={!r}, set={!r}, number={!r}, rarity={!r}, faces={!r}, condition={!r}, foil={!r}, count={!r})'
        return fmt.format(self.id, self.set, self.number, self.rarity, self.faces, self.condition, self.foil, self.count)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['condition'] = self.condition.symbol
        d['foil'] = self.foil
        d['count'] = self.count
        return d

def image_slug(c: Card, size: Union[Size, str], format: str=None, front: bool=True, lang: str='en') -> str:
    """Get the file name of a version of the card's image file.
    
    :param c: The card whose image to be shown. Must contain at least a set and
    collector number.
    :param size: The size of image to link to. Can be one of 'full', 'large',
    'normal', or 'small'. Not case-sensitive. Can also be a Size object.
    :param format: The file format for the file. By default, will be determined
    by the size; 'full' will be 'png' and all others will be 'jpg'. If format is
    set to a non-None value, this behavior is overriden and the passed-in format
    is used instead. Not case-sensitive.
    :param front: Whether the image should be for the front of the card. If set
    to False and the card does not contain a back face, the generic 'mtg card
    back' file name is printed.
    :param lang: The region code of the language of card that should be shown.
    Not case-sensitive.
    """
    if not isinstance(size, Size):
        size = size_from_str(size)

    if format is not None:
        if format.lower() not in ['png', 'jpg', 'jpeg']:
            err = "Invalid format for card image; must be one of 'png' or 'jpg'"
            err += " but was: {!r}".format(format)
            raise ValueError(err)
        format = format.lower()
        if format == 'jpeg':
            format = 'jpg'
    else:
        format = size.format

    if c.number is None or c.number == '':
        raise ValueError("Card does not have collector number set")
    
    if c.set is None or c.set == '':
        raise ValueError("Card does not have set code set")
    
    # check generic backface
    face = "front"
    if not front:
        if len(c.faces) < 2:
            # this card doesn't have a back; show generic back face
            return 'back.{:s}'.format(format)
        else:
            face = "back"

    # args have been checked now show image
    s = '{0:s}-{1:s}-{2:s}-{3:s}-{4:s}.{5:s}'
    return s.format(
        c.set.upper(),
        c.pretty_num,
        face,
        size.name,
        lang,
        format
    )