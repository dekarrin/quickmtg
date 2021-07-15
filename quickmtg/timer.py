from datetime import timedelta
import time

class PeriodTimer:
    """Contains methods for coordinating actions that need to run on a periodic
    basis. This class allows a period to be defined, and once started, next()
    can be called to wait until the end of the current period. This can be used
    to provide a 'frame-limiter' of code execution, and can be used for any
    operation that requires actions not occur too quickly, such as applying
    anti-flood measures to requests.
    
    Create a PeriodTimer by providing a timedelta, then use start() to begin it.
    Perform an operation, than call next() to wait until the start of the next
    period.
    """
    
    def __init__(self, period: timedelta):
        """Create a new PeriodTimer. It will not start counting until start() or
        next() is called."""
        self.period: timedelta = period
        self._running: bool = False
        self._period_start: float = 0

    @property
    def running(self) -> bool:
        """Return whether the timer is currently running. This will be true from
        the first call to either next() or start() up until stop() is called."""
        return self._running

    def start(self):
        """Begin the timer. If it has already been started, this method has no
        effect."""
        if self.running:
            return
        self._period_start = time.monotonic()
        self._running = True

    def next(self):
        """Wait until the start of the next period. If the timer has not yet
        been started with a call to start(), it is started automatically and the
        first period is immediately skipped."""
        if not self.running:
            self.start()
            return
        
        now = time.monotonic()
        wait_time = self._target() - now
        
        if wait_time < 0:
            # find out how many periods we missed
            missed_periods = int(wait_time // self.period.total_seconds())
            # use that to set the period start (and thus _target time) for next
            # period and immediately return.
            self._period_start += (missed_periods * self.period).total_seconds()
            return
            
        time.sleep(wait_time)
        self._period_start += self.period.total_seconds()

    def stop(self):
        """Stop the running timer."""
        self._running = False

    def _target(self) -> float:
        return self._period_start + self.period.total_seconds()

