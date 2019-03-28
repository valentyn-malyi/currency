from currency.currency import Currency
from datetime import datetime
import numpy
from typing import Generator, Tuple,List


def result(curr: Currency, mean: numpy.array, time: datetime, take: int, stop: int) -> \
        Generator[Tuple[float, str, int], None, None]:
    for d in range(len(mean)):
        state: str = "NONE"
        close, high, low = curr.get_high_low(time=time, n=len(mean))
        mean = -mean
        if mean[d] > 0:
            for i in range(d):
                if high[i] > mean[i] + take:
                    res = mean[i] + take
                    state = "TAKE"
                    break
                if low[i] < mean[i] - stop:
                    res = mean[i] - stop
                    state = "STOP"
                    break
            else:
                res = close[d]
        else:
            for i in range(d):
                if high[i] > mean[i] + stop:
                    state = "STOP"
                    res = -mean[i] - stop
                    break
                if low[i] < mean[i] - take:
                    state = "TAKE"
                    res = -mean[i] + take
                    break
            else:
                res = -close[d]
        yield res, state, d


def main(currs: List[Currency], start: datetime, end: datetime, probability: float, number_bars: int):
    for curr in currs:
        for current_bar in curr.right(time=start, n=999999999):
            current_time = current_bar.time
            if current_time >= end:
                break
            n = len(array[0])
            delta = self.period.delta * n
            deq = deque(maxlen=n)
            last_time = datetime.min
            last_time = last_time.replace(tzinfo=timezone('UTC'))
            for bar in self.left(time=time - delta, n=self.period.number_bars):
                deq.append(bar.close)
            if len(deq) < n or bar.time - last_time < delta:
                continue
            corrcoef = numpy.corrcoef(array, deq)[0, 1]
            if abs(corrcoef) > probability:
                last_time = bar.time
                yield Similar(bar=bar, corrcoef=corrcoef, n=n)
