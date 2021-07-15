import uuid

class Card:
	def __init__(self, id: uuid.UUID, cmc: int):
		self.id = id
		self.cmc = cmc