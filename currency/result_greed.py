from currency.currency import Currency
from datetime import datetime
import numpy
import bisect
from typing import Tuple, Union


# import matplotlib.pyplot as plt


def destrib(a: numpy.array, x: float):
    n = len(a)
    bisect_right = bisect.bisect_right(a, x)
    bisect_left = bisect.bisect_left(a, x)
    if bisect_right != bisect_left:
        return bisect_left / n
    bisect_left += -1
    if bisect_right == n:
        return 1
    if bisect_left == -1:
        return 0
    else:
        return (bisect_left + (x - a[bisect_left]) / (a[bisect_right] - a[bisect_left])) / n


def result(curr: Currency, greed: numpy.array, time: datetime, number_bars: int, enter: float, stop_coef: float,
           skip_open: int, skip_close: int) -> \
        Tuple[float, str, Union[int, None], int, str]:
    close, high, low = curr.get_high_low(time=time, n=number_bars)
    enter = min(max(0.01, enter), 0.2)
    for i in range(1, number_bars - skip_open):
        g = greed[:, i - 1]
        g.sort()
        if destrib(a=g, x=close[i - 1]) > 1 - enter and close[i - 1] > 0:
            stop = (stop_coef + 1) * close[i - 1]
            for skip_day_i in range(skip_open):
                if high[i + skip_open] > stop:
                    return 0, "SKIP_DAY", i, skip_day_i, "SELL"
            offer = close[i + skip_open]
            if offer > 0 and offer - stop < 0:
                for j in range(i + skip_open, number_bars):
                    if high[j] > stop:
                        return offer - stop, "STOP", i, j - i - skip_open, "SELL"
                    if low[j] < 0:
                        return offer, "TAKE", i, j - i - skip_open, "SELL"
                    if j - i >= skip_close:
                        return offer - close[j], "None", i, j - i - skip_open, "SELL"
                return offer - close[number_bars - 1], "None", i, number_bars - i - skip_open, "SELL"
            else:
                return 0, "MISS", i, skip_open, "SELL"

        if destrib(a=g, x=close[i - 1]) < enter and close[i - 1] < 0:
            stop = (stop_coef + 1) * close[i - 1]
            for skip_day_i in range(skip_open):
                if low[i + skip_day_i] < stop:
                    return 0, "SIGNAL", i, skip_day_i, "BUY"
            offer = close[i + skip_open]
            if offer < 0 and stop - offer < 0:
                for j in range(i + skip_open, number_bars):
                    if low[j] < stop:
                        return stop - offer, "STOP", i, j - i - skip_open, "BUY"
                    if high[j] > 0:
                        return - offer, "TAKE", i, j - i - skip_open, "BUY"
                    if j - i >= skip_close:
                        return -offer + close[j], "None", i, j - i - skip_open, "BUY"
                return -offer + close[number_bars - 1], "None", i, number_bars - i - skip_open, "BUY"
            else:
                return 0, "MISS", i, skip_open, "BUY"
    return 0, "", None, -1, ""


def main(curr: Currency, start: datetime, end: datetime, probability: float, number_bars: int, history_min: int,
         enter: float, stop_coef: float, skip_open: int, skip_close: int):
    for current_bar in curr.right(time=start, n=999999999):
        current_time = current_bar.time
        print(current_time)
        if current_time >= end:
            break
        array = []
        for bar in curr.left(time=current_time, n=number_bars):
            array.append(bar.close)
        array = numpy.array(array)
        greed = []
        for slice in curr.slices(array=array, time=current_time, probability=probability):
            close, _, _ = curr.get_high_low(time=slice.time, n=number_bars)
            greed.append(close)
        greed = numpy.array(greed)
        if len(greed) < history_min:
            continue
        res, state, d, open_d, sb = result(
            curr=curr, greed=greed, time=current_time, number_bars=number_bars, enter=enter, stop_coef=stop_coef,
            skip_open=skip_open, skip_close=skip_close)

        if d is not None:
            yield [current_time.replace(tzinfo=None), res, state, len(greed), d, open_d, sb]
