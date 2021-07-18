from . import color
from .color import Color
from typing import Any, Dict, List, Optional, Set
import uuid

class Face:
	def __init__(self, **kwargs):
		self.name = ''
		self.type = ''
		self.cost = ''
		self.text = ''

		if kwargs is not None:
			if 'name' in kwargs:
				self.name = kwargs['name']
			if 'type' in kwargs:
				self.type = kwargs['type']
			if 'cost' in kwargs:
				self.cost = kwargs['cost']
			if 'text' in kwargs:
				self.text = kwargs['text']

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
			'text': self.text
		}


class Card:
	def __init__(self, **kwargs):
		self.id: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
		self.set: str = ''
		self.rarity: str = ''
		self.faces: List[Face] = list()

		if kwargs is not None:
			if 'id' in kwargs:
				self.id = kwargs['id']
			if 'set' in kwargs:
				self.set = kwargs['set']
			if 'rarity' in kwargs:
				self.rarity = kwargs['rarity']
			if 'faces' in kwargs:
				self.faces = list(Face(**f) for f in kwargs['faces'])

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
	
	def to_dict(self) -> Dict[str, Any]:
		return {
			'id': self.id,
			'set': self.set,
			'rarity': self.rarity,
			'faces': [f.to_dict() for f in self.faces]
		}