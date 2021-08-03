import json
from quickmtg import scryfall
import uuid

from .card import Card, OwnedCard, Condition, MINT
from . import util
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Union

# duplicates many properties of OwnedCard because ownedCard should be immutable
# TODO: make ownedCard immutable than replace this class usage with OwnedCard in
# inventory.

class _CardData:
    """
    Instances of this class should be considered immutable and should never
    change.
    """
    def __init__(self, **kwargs):
        self._card: Card = None
        self._condition: Condition = MINT
        self._foil: bool = False
        self._count: int = 0
        self._locations: FrozenSet[str] = set()

        if 'card' in kwargs:
            c = kwargs['card']
            if isinstance(c, Card):
                self._card = c
            else:
                self._card = Card(**c)
        if 'condition' in kwargs:
            self._condition = str(kwargs['condition'])
        if 'foil' in kwargs:
            self._foil = kwargs['foil']
        if 'count' in kwargs:
            self._count = int(kwargs['count'])
        if 'locations' in kwargs:
            self._locations = frozenset(kwargs['locations'])

    @property
    def card(self) -> Card:
        return self._card

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def foil(self) -> bool:
        return self._foil
    
    @property
    def count(self) -> int:
        return self._count

    @property
    def locations(self) -> FrozenSet[str]:
        return self._locations

    def with_count(self, new_count: int) -> '_CardData':
        """
        Return a Card data with the given count.
        """
        d = self.to_dict()
        d['count'] = new_count
        return _CardData(**d)

    def with_locations(self, new_locations: Sequence[str]) -> '_CardData':
        """
        Return a Card data with the given locations set.
        """
        d = self.to_dict()
        d['locations'] = list(new_locations)
        return _CardData(**d)

    def __eq__(self, other) -> bool:
        if not isinstance(other, _CardData):
            return False

        if self.card != other.card:
            return False
        if self.condition != other.condition:
            return False
        if self.foil != other.foil:
            return False
        if self.count != other.count:
            return False
        if self.locations != other.locations:
            return False
        
        return True

    def __hash__(self) -> int:
        return hash((self.card, self.condition, self.foil, self.count, self.locations))

    def __str__(self) -> str:
        s = "_CardData<card: {!s}, condition: {!s}, foil: {!s}, count: {!s}, locations: {!s}>"
        return s.format(self.card, self.condition, self.foil, self.count, self.locations)

    def __repr__(self) -> str:
        s = "_CardData(card={!r}, condition={!r}, foil={!r}, count={!r}, locations={!r})"
        return s.format(self.card, self.condition, self.foil, self.count, self.locations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'card': self.card.to_dict(),
            'condition': self.condition,
            'foil': self.foil,
            'count': self.count,
            'locations': list(self.locations)
        }

class Inventory:
    def __init__(self, **kwargs):
        """
        Create a new Inventory object. Kwargs can contain each of the properties
        of this Inventory, and if passed in the spread output of to_dict(), will
        recreate the original Inventory.
        """
        self.id: str = ''
        self.name: str = ''
        self.path: str = ''

        # card scryfall ID -> foilcond -> card
        self._cards: Dict[uuid.UUID, Dict[str, _CardData]] = dict()

        if 'id' in kwargs:
            self.id = kwargs['id']
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'path' in kwargs:
            self.path = kwargs['path']
        if 'cards' in kwargs:
            cards = kwargs['cards']
            if isinstance(cards, dict):
                for k, card_versions in cards:
                    cid = uuid.UUID(str(k))
                    self._cards[cid] = dict()
                    for foilcond, version in card_versions:
                        self._cards[cid][str(foilcond)] = _CardData(**version)
            else:
                # assume its sequencable at least
                for c in cards:
                    if isinstance(c, OwnedCard):
                        self.add_card(c)
                    else:
                        self.add_card(OwnedCard(**c))

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = util.normalize_id(value)

    @property
    def cards(self) -> Set[OwnedCard]:
        """
        Convert entire card store to just a set.
        """
        cards_set = set()
        for scryfall_id in self._cards:
            owned_versions = self._cards[scryfall_id]
            for owned_version_key in owned_versions:
                owned_version = owned_versions[owned_version_key]
                data = owned_version.card.to_dict()
                data['condition'] = owned_version.condition
                data['foil'] = owned_version.foil
                data['count'] = owned_version.count
                data['locations'] = owned_version.locations
                cards_set.add(OwnedCard(**data))
        return cards_set

    def __eq__(self, other) -> bool:
        if not isinstance(other, Inventory):
            return False

        if self.id != other.id:
            return False
        if self.name != other.name:
            return False
        if self.path != other.path:
            return False
        if self.cards != other.cards:
            return False
        
        return True

    def __hash__(self) -> int:
        return hash((self.id, self.name, self.path, frozenset(self.cards)))

    def __str__(self) -> str:
        s = "Inventory<id: {!s}, name: {!s}, path: {!s}, cards: {!s}>"
        return s.format(self.id, self.name, self.path, self.cards)

    def __repr__(self) -> str:
        s = "Inventory(id={!r}, name={!r}, path={!r}, cards={!r})"
        return s.format(self.id, self.name, self.path, self.cards)

    def add_card(self, c: OwnedCard, locations: Optional[Sequence[str]]=None):
        """Add an owned card to this inventory. If the card variety has already
        been added, the existing locations and counts are updated to include the
        newly-added card.
        
        TODO: use OwnedCard.locations instead of locations param once _CardData
        is removed.
        """
        if c.id not in self._cards:
            self._cards[c.id] = dict()
        
        foilcond = '{:s}FOIL/{:s}'.format("" if c.foil else "NON-", c.condition.name)
        if foilcond not in self._cards[c.id]:
            cd = _CardData(card=Card(**c.to_dict()), foil=c.foil, condition=c.condition, count=0)
            self._cards[c.id][foilcond] = cd
        
        old_cd = self._cards[c.id][foilcond]
        new_locs = set(old_cd.locations)
        new_locs.update(locations)
        new_cd = old_cd.with_count(old_cd.count + c.count).with_locations(new_locs)
        
        self._cards[c.id][foilcond] = new_cd

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this Inventory to a dict suitable for storage or pickling.

        Inventory(**i.to_dict()) is gauranteed to return a Inventory that
        compares equal to the original Inventory.
        """
        d = {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'cards': {
                str(cid): {
                    foilcond: c.to_dict() for foilcond, c in cval
                } for cid, cval in self._cards
            }
        }
        return d

    def to_file(self, file_path: str):
        """
        Save the current contents of this inventory to a pretty-printed JSON
        file located at the given path.

        :param file_path: Path to the file to save the contents of this
        Inventory in on disk. If a file already exists, it will be overriden.
        """
        with open(file_path, 'w') as fp:
            json.dump(self.to_dict(), fp, indent=4)


class Metadata:
    def __init__(self, **kwargs):
        """
        Create a new Metadata object. Kwargs can contain each of the properties
        of this Metadata, and if passed in the spread output of to_dict(), will
        recreate the original Metadata.
        """
        self.ids: Set[str] = set()

        if 'ids' in kwargs:
            self.ids = set(kwargs['ids'])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Metadata):
            return False

        if self.ids != other.ids:
            return False
        
        return True

    def __hash__(self) -> int:
        return hash(frozenset(self.ids))

    def __str__(self) -> str:
        s = "Metadata<ids: {!s}>"
        return s.format(self.ids)

    def __repr__(self) -> str:
        s = "Metadata(ids={!r})"
        return s.format(self.ids)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this Metadata to a dict suitable for storage or pickling.

        Metadata(**m.to_dict()) is gauranteed to return a Metadata that compares
        equal to the original Metadata.
        """
        d = {
            'ids': self.ids,
        }
        return d


def from_file(file_path: str) -> Inventory:
    """
    Load an invetory from a JSON file on disk. It must be in the format of a
    file created with a call to Inventory.to_file().

    :param file_path: The path to the file to load.
    """
    with open(file_path, 'r') as fp:
        inven_dict = json.load(fp)

    return Inventory(**inven_dict)
