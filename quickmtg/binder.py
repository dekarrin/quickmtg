from .card import Card, OwnedCard
from typing import Any, Dict, List, Optional, Sequence, Union
import re
import json


class Binder:
    def __init__(self, **kwargs):
        """
        Create a new Binder object. Kwargs can contain each of the properties
        of this Binder, and if passed in the spread output of to_dict(), will
        recreate the original Binder.
        """
        self.id: str = ''
        self.name: str = ''
        self.path: str = ''
        self.cards: List[OwnedCard] = list()

        if 'id' in kwargs:
            self.id = re.sub(r'[^a-z0-9_]', '_', str(kwargs['id']).lower())
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'path' in kwargs:
            self.path = kwargs['path']
        if 'cards' in kwargs:
            cards_list = kwargs['cards']
            for c in cards_list:
                if isinstance(c, OwnedCard):
                    self.cards.append(c)
                else:
                    # assume it's a dict
                    converted_card = OwnedCard(**c)
                    self.cards.append(converted_card)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Binder):
            return False

        if self.id != other.id:
            return False
        if self.name != other.name:
            return False
        if self.path != other.path:
            return False
        if len(self.cards) != len(other.cards):
            return False
        for my_card, other_card in zip(self.cards, other.cards):
            if my_card != other_card:
                return False
        
        return True

    def __hash__(self) -> int:
        return hash((self.id, self.name, self.path, frozenset(self.cards)))

    def __str__(self) -> str:
        s = "Binder<id: {!s}, name: {!s}, path: {!s}, cards: {!s}>"
        return s.format(self.id, self.name, self.path, self.cards)

    def __repr__(self) -> str:
        s = "Binder(id={!r}, name={!r}, path={!r}, cards={!r})"
        return s.format(self.id, self.name, self.path, self.cards)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this Binder to a dict suitable for storage or pickling.

        Binder(**b.to_dict()) is gauranteed to return a Binder that compares
        equal to the original Binder.
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
        Save the current contents of this binder to a pretty-printed JSON file
        located at the given path.

        :param file_path: Path to the file to save the contents of this Binder
        in on disk. If a file already exists, it will be overriden.
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
        self.ids: List[str] = list()

        if 'ids' in kwargs:
            self.ids = list(kwargs['ids'])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Metadata):
            return False

        if len(self.ids) != len(other.ids):
            return False
        for my_id, other_id in zip(self.ids, other.ids):
            if my_id != other_id:
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


def from_file(file_path: str) -> Binder:
    """
    Load a binder from a JSON file on disk. It must be in the format of a file
    created with a call to Binder.to_file().

    :param file_path: The path to the file to load.
    """
    with open(file_path, 'r') as fp:
        binder_dict = json.load(fp)

    return Binder(**binder_dict)