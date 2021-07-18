from enum import Enum
from typing import Set

class Color:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash((self.name, self.symbol,))

WHITE = Color('WHITE', 'W')
BLUE = Color('BLUE', 'U')
BLACK = Color('BLACK', 'B')
RED = Color('RED', 'R')
GREEN = Color('GREEN', 'G')

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

