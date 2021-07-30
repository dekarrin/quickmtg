import typing
import uuid
from datetime import datetime

class SetType:
    _all: typing.Set = set()

    def __init__(self, api_name: str, desc: str):
        self.name = str(api_name)
        self.desc = desc
        SetType._all.add(self)

    def __eq__(self, other):
        if not isinstance(other, SetType):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name.lower()

    @staticmethod
    def parse(name: str) -> 'SetType':
        for s in SetType._all:
            if s.name == name:
                return s
        return None

TypeCore = SetType('core', 'A yearly Magic core set (Tenth Edition, etc)')
TypeExpansion = SetType('expansion', 'A rotational expansion set in a block (Zendikar, etc)')
TypeMasters = SetType('masters', 'A reprint set that contains no new cards (Modern Masters, etc)')
TypeMasterpiece = SetType('masterpiece', 'Masterpiece Series premium foil cards')
TypeFromTheVault = SetType('from_the_vault', 'From the Vault gift sets')
TypeSpellbook = SetType('spellbook', 'Spellbook series gift sets')
TypePremiumDeck = SetType('premium_deck', 'Premium Deck Series decks')
TypeDuelDeck = SetType('duel_deck', 'Duel Decks')
TypeDraftInnovation = SetType('draft_innovation', 'Special draft sets, like Conspiracy and Battlebond')
TypeTreasureChest = SetType('treasure_chest', 'Magic Online treasure chest prize sets')
TypeCommander = SetType('commander', 'Commander preconstructed decks')
TypePlanechase = SetType('plainchase', 'Planechase sets')
TypeArchenemy = SetType('archenemy', 'Archenemy sets')
TypeVanguard = SetType('vanguard', 'Vanguard card sets')
TypeFunny = SetType('funny', 'A funny un-set or set with funny promos (Unglued, Happy Holidays, etc)')
TypeStarter = SetType('starter', 'A starter/introductory set (Portal, etc)')
TypeBox = SetType('box', 'A gift box set')
TypePromo = SetType('promo', 'A set that contains purely promotional cards')
TypeToken = SetType('token', 'A set made up of tokens and emblems.')
TypeMemorabilia = SetType('memorabilia', 'A set made up of gold-bordered, oversize, or trophy cards that are not legal')


class Set:
    """
    Represents a group of related MTG cards. Not all are from official releases,
    some are for grouping purposes only. All are provided by data from Scryfall.

    :ivar id: Scryfall ID of this set.
    :ivar code: The unique three to five-letter code for this set.
    :ivar name: English language name for the set.
    """

    def __init__(self, **kwargs):
        self.id: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
        self.code: str = ''
        self.name: str = ''
        self.type: SetType = TypeCore
        self.release_date: datetime = datetime.min
        self.block: str = ''
        self.parent_set: str = ''
        self.card_count: int = 0
        self.digital: bool = False
        self.foil_only: bool = False
        self.nonfoil_only: bool = False

        if kwargs is not None:
            if 'id' in kwargs:
                id = kwargs['id']
                if isinstance(id, uuid.UUID):
                    self.id = id
                else:
                    self.id = uuid.UUID(kwargs['id'])
            if 'code' in kwargs:
                self.code = str(kwargs['code'])
            if 'name' in kwargs:
                self.name = str(kwargs['name'])
            if 'type' in kwargs:
                t = kwargs['type']
                if isinstance(t, SetType):
                    self.type = t
                else:
                    self.type = SetType.parse(str(t))
            if 'release_date' in kwargs:
                rd = kwargs['release_date']
                if isinstance(rd, datetime):
                    self.release_date = rd
                else:
                    self.release_date = datetime.fromisoformat(str(rd))
                self.number = kwargs['number']
            if 'block' in kwargs:
                self.block = str(kwargs['block'])
            if 'parent_set' in kwargs:
                self.parent_set = str(kwargs['parent_set'])
            if 'card_count' in kwargs:
                self.card_count = int(kwargs['card_count'])
            if 'digital' in kwargs:
                self.digital = bool(kwargs['digital'])
            if 'foil_only' in kwargs:
                self.foil_only = bool(kwargs['foil_only'])
            if 'nonfoil_only' in kwargs:
                self.nonfoil_only = bool(kwargs['nonfoil_only'])

    def __hash__(self) -> int:
        return hash((self.id, self.code))

    def __eq__(self, other):
        if not isinstance(other, Set):
            return NotImplemented

        return (self.id, self.code) == (other.id, other.code)

    def __ne__(self, other):
        if not isinstance(other, Set):
            return NotImplemented

        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
            
        return (self.type.name, self.release_date, self.name) < (other.type.name, other.release_date, other.name) 

    def __le__(self, other):
        if not isinstance(other, Set):
            return NotImplemented

        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        if not isinstance(other, Set):
            return NotImplemented

        return not self.__lt__(other)

    def __gt__(self, other):
        if not isinstance(other, Set):
            return NotImplemented

        return not self.__le__(other)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        s = 'Set(id={!r}, code={!r}, name={!r}, type={!r}, release_date={!r}, '
        s += 'block={!r}, parent_set={!r}, card_count={!r}, digital={!r}, '
        s += 'foil_only={!r}, nonfoil_only={!r})'

        return s.format(
            self.id,
            self.code,
            self.name,
            self.type,
            self.release_date,
            self.block,
            self.parent_set,
            self.card_count,
            self.digital,
            self.foil_only,
            self.nonfoil_only,
        )

    @property
    def has_foils(self) -> bool:
        return not self.nonfoil_only

    @property
    def has_nonfoils(self) -> bool:
        return not self.foil_only

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        d = {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'release_date': self.release_date.isoformat(),
            'block': self.block,
            'parent_set': self.parent_set,
            'card_count': self.card_count,
            'digital': self.digital,
            'foil_only': self.foil_only,
            'nonfoil_only': self.nonfoil_only
        }
        return d
