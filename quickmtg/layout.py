
import math

from jinja2.utils import select_autoescape
from . import filters
from quickmtg.card import SizeSmall, image_slug, size_from_str, Card
from typing import Any, Callable, Dict, Iterable, Optional, Sequence
import jinja2

_jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader("quickmtg"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)
_jinja_env.filters['cardfile'] = filters.get_image_slug
_jinja_env.filters['sizeh'] = filters.size_height
_jinja_env.filters['sizew'] = filters.size_width

"""gen_x functions end in newline, make_x funcs do not"""

def gen_index_page() -> str:
    template = _jinja_env.get_template('view/index.html.jinja')
    return template.render(binder_name="default")

def gen_binder_page(cards: Sequence[Dict[str, Any]], pageno: int, total_pages: int, rows: int, cols: int):
    template = _jinja_env.get_template('view/binder.html.jinja')

    card_rows = list()
    for y in range(rows):
        row = list()
        for x in range(cols):
            idx = y*cols + x
            c = cards[idx]
            row.append(c)
        card_rows.append(row)

    data = {
        'binder_name': "default",
        'page_number': pageno,
        'total_pages': total_pages,
        'cards': card_rows
    }

    return template.render(data)