from . import color
from .color import Color
from typing import Any, Dict, List, Optional, Set
import uuid


class Condition:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash((self.name, self.symbol,))

MINT = Condition('MINT/NEAR MINT', '')
SLIGHTLY_USED = Condition('SLIGHTLY USED', 'SL')
MEDIUM_USED = Condition('MEDIUM USED', 'ME')
HEAVY_USED = Condition('HEAVY USED', 'HE')


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
        self.rarity: str = ''
        self.faces: List[Face] = list()
        self.number: int = 0

        if kwargs is not None:
            if 'id' in kwargs:
                self.id = kwargs['id']
            if 'set' in kwargs:
                self.set = kwargs['set']
            if 'rarity' in kwargs:
                self.rarity = kwargs['rarity']
            if 'faces' in kwargs:
                self.faces = list(Face(**f) for f in kwargs['faces'])
            if 'number' in kwargs:
                self.number = int(kwargs['number'])

    @property
    def name(self) -> str:
        if len(self.faces) < 1:
            return ""
        n = self.faces[0].name
        for face in self.faces[1:]:
            n += " // " + face.name
        return n

    @property
    def type(self) -> str:
        if len(self.faces) < 1:
            return ""
        t = self.faces[0].type
        for face in self.faces[1:]:
            t += " // " + face.type
        return t

    @property
    def cost(self) -> str:
        if len(self.faces) < 1:
            return ""
        c = self.faces[0].cost
        for face in self.faces[1:]:
            c += " // " + face.cost
        return c

    @property
    def text(self) -> str:
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
        if len(self.faces) < 1:
            return set()
        s = self.faces[0].color
        for face in self.faces[1:]:
            s.update(face.color)
        return s

    @property
    def power(self) -> List[Optional[str]]:
        if len(self.faces) < 1:
            return list()
        p = list(self.faces[0].power)
        for face in self.faces[1:]:
            p.append(face.power)
        return p

    @property
    def toughness(self) -> List[Optional[str]]:
        if len(self.faces) < 1:
            return list()
        t = list(self.faces[0].toughness)
        for face in self.faces[1:]:
            t.append(face.toughness)
        return t
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'set': self.set,
            'rarity': self.rarity,
            'faces': [f.to_dict() for f in self.faces],
            'number': self.number
        }

class OwnedCard(Card):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.condition: Condition = None
        self.foil: bool = False

        if kwargs is not None:
            if 'condition' in kwargs:
                c = kwargs['condition']
                if isinstance(c, Condition):
                    self.condition = c
                else:
                    self.condition = cond_from_symbol(c)
            if 'foil' in kwargs:
                self.foil = kwargs['foil']

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['condition'] = self.condition.symbol
        d['foil'] = self.foil
        return d