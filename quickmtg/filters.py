from . import card

def get_image_slug(value, size: str="small"):
    if not isinstance(value, card.Card):
        return "ERROR[NOT_A_CARD({!r})]".format(value)
    try:
        s = card.size_from_str(size)
    except TypeError:
        return "ERROR[INVALID_SIZE({!r})]".format(size)

    try:
        return card.image_slug(value, s)
    except Exception as e:
        return "ERROR[{!s}]".format(e)

def size_width(value):
    try:
        s = card.size_from_str(value)
    except TypeError:
        return "ERROR[INVALID_SIZE({!r})]".format(value)

    return str(s.w)

def size_height(value):
    try:
        s = card.size_from_str(value)
    except TypeError:
        return "ERROR[INVALID_SIZE({!r})]".format(value)

    return str(s.h)