import datetime
import time
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')

class _TimeLimitedFuncCall(Generic[T]):
    def __init__(self, period: datetime.timedelta, fn: Callable[[], T], call_then_wait: bool=False):
        self.period = period
        self.fn = fn
        self.next_call = time.monotonic()
        if not call_then_wait:
            self.next_call += period.total_seconds()
    
    def __call__(self) -> Optional[T]:
        if time.monotonic() >= self.next_call:
            val = self.fn()
            self.next_call = time.monotonic() + self.period.total_seconds()
            return val
        else:
            return None

def once_every(period: datetime.timedelta, fn: Callable[[], T]) -> Callable[[], Optional[T]]:
    """
    Return a 'check' function that performs the given function only once every
    period.

    The returned function can be called as often as desired, but the embedded
    function fn is only called once the given period has elapsed. Once fn has
    been called once, it will not be called until the period has again elapsed,
    and so on indefinitely.

    The returned function could be called in a for-loop to do something like
    show status. Example:

    current = 0
    status = lambda: print("{:.2f}% done!".format(current / len(items)))
    show_status = once_every(timedelta(seconds=10), status)

    for item in items:
        show_status()  # status() will only be called once every 10 seconds
        do_work(item)
    """
    return _TimeLimitedFuncCall(period, fn, False)

