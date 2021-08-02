import json

from .card import Card, OwnedCard
from . import util
from typing import Any, Dict, List, Optional, Sequence, Set, Union

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
        self.cards: Set[OwnedCard] = set()

        if 'id' in kwargs:
            self.id = kwargs['id']
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'path' in kwargs:
            self.path = kwargs['path']
        if 'cards' in kwargs:
            cards_list = kwargs['cards']
            for c in cards_list:
                if isinstance(c, OwnedCard):
                    self.cards.add(c)
                else:
                    # assume it's a dict
                    converted_card = OwnedCard(**c)
                    self.cards.add(converted_card)

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = util.normalize_id(value)

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
            'cards': [c.to_dict() for c in self.cards]
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
