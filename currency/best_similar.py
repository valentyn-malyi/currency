from currency.utils import Currency, Bar
from datetime import datetime
import numpy
from typing import Generator, Tuple, List


def result(curr: Currency, best_bar: Bar, time: datetime, take: int, stop: int, number_bars: int) -> \
        Generator[Tuple[float, str, int], None, None]:
    close, high, low = curr.get_high_low(time=time, n=number_bars)
    mean, _, _ = curr.get_high_low(time=best_bar.time, n=number_bars)
    for d in range(number_bars):
        state: str = "NONE"
        if mean[d] > 0:
            for i in range(d):
                if low[i] < mean[i] - stop:
                    res = mean[i] - stop
                    state = "STOP"
                    break
                if high[i] > mean[i] + take:
                    res = mean[i] + take
                    state = "TAKE"
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

        yield res, state, d, mean[d]


def main(currs: List[Currency], start: datetime, end: datetime, probability: float, number_bars: int, take: int,
         stop: int):
    delta = 2 * currs[0].period.delta * number_bars
    current_bar = currs[0].right(time=start, n=999999999)

    while True:
        current_time = next(current_bar).time
        if current_time >= end:
            break
        best_bar = None
        best_corrcoef = 0
        array = []
        print(current_time)

        for num_curr in range(len(currs)):
            curr_array = []
            for bar in currs[num_curr].left(time=current_time, n=number_bars):
                curr_array.append(bar.close)
            array.append(curr_array)

        for take_bar in currs[0].left(time=current_time - delta, n=number_bars):

            best_corrcoef2 = 1
            index = True

            for num_curr in range(len(currs)):

                curr = currs[num_curr]
                array2 = []
                for bar in curr.left(time=take_bar.time, n=number_bars):
                    array2.append(bar.close)
                corrcoef = numpy.corrcoef(array[num_curr], array2)[0, 1]
                if corrcoef > probability:
                    best_corrcoef2 *= corrcoef
                else:
                    index = False
                    break

            if index:
                best_corrcoef = max(best_corrcoef, best_corrcoef2)
                best_bar = take_bar

        if best_bar is not None:
            for num_curr in range(len(currs)):
                for res, state, d, m in result(curr=currs[num_curr], best_bar=best_bar, time=current_time,
                                               number_bars=number_bars, take=take, stop=stop):
                    yield [currs[num_curr].name, current_time.replace(tzinfo=None), res, d, state, m]
