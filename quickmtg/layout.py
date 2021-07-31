
import math

from jinja2.utils import select_autoescape
from . import filters
from quickmtg.card import SizeSmall, image_slug, size_from_str, Card
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import jinja2
import logging
import os

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

_jinja_loader = jinja2.PackageLoader("quickmtg")

_jinja_env = jinja2.Environment(
    loader=_jinja_loader,
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


_jinja_env.filters['cardfile'] = filters.get_image_slug
_jinja_env.filters['sizeh'] = filters.size_height
_jinja_env.filters['sizew'] = filters.size_width

def gen_static() -> List[Dict[str, Union[str, bytes]]]:
    """
    Return write_mode, data. data is either bytes or str, and write_mode will be
    'b' or '' to reflect this."""
    results = list()
    # TODO: dynamically load these using jinja's loader if possible
    files = ['styles.css', 'flip.svg', 'flip.png']
    text_files = ['css', 'html', 'js', 'svg']
    for f in files:
        if any(('.' + ext) in f for ext in text_files):
            mode = ''
            template = _jinja_env.get_template('_static/' + f)
            data = template.render()
        else:
            this_path = os.path.dirname(__file__)
            mode = 'b'
            data = b''
            _log.error("writing out to: {!s}".format(fname))
            with open(fname, 'rb') as fp:
                data = fp.read()
            _log.error("siz {:d}".format(len(data)))

        r = {
            'name': f,
            'data': data,
            'write_mode': mode
        }
        results.append(r)
    return results

def gen_index_page(binder_name="default") -> str:
    template = _jinja_env.get_template('view/index.html.jinja')
    return template.render(binder_name=binder_name)

def gen_binder_page(
    cards: Sequence[Dict[str, Any]],
    pageno: int,
    total_pages: int,
    rows: int,
    cols: int,
    binder_name="default"
):
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
        'binder_name': binder_name,
        'page_number': pageno,
        'total_pages': total_pages,
        'cards': card_rows
    }

    return template.render(data)