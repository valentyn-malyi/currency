from currency.currency import Currency
from datetime import datetime
import numpy
import bisect
from typing import Generator, Tuple, List
import matplotlib.pyplot as plt


def destrib(a: numpy.array, x: float):
    n = len(a)
    r = bisect.bisect_right(a, x)
    l = bisect.bisect_left(a, x)
    if r != l:
        return l / n
    l += -1
    if r == n:
        return 1
    if l == -1:
        return 0
    else:
        return (l + (x - a[l]) / (a[r] - a[l])) / n


def result(curr: Currency, greed: numpy.array, time: datetime, number_bars: int, enter: float) -> \
        Tuple[float, str, int, int, str]:
    close, high, low = curr.get_high_low(time=time, n=number_bars)
    enter = min(max(0.01, enter), 0.2)
    for i in range(1, number_bars):
        g = greed[:, i - 1]
        g.sort()
        if destrib(a=g, x=close[i - 1]) > 1 - enter and close[i - 1] > 0:
            take = close[i - 1]
            for j in range(i, number_bars):
                if high[j] > 2 * take:
                    return -take, "STOP", i, j - i, "SELL"
                if low[j] < 0:
                    return take, "TAKE", i, j - i, "SELL"
            return take - close[number_bars - 1], "None", i, number_bars - i, "SELL"
        if destrib(a=g, x=close[i - 1]) < enter and close[i - 1] < 0:
            take = -close[i - 1]
            for j in range(i, number_bars):
                if low[j] < -2 * take:
                    return -take, "STOP", i, j - i, "BUY"
                if high[j] > 0:
                    return take, "TAKE", i, j - i, "BUY"

            return close[number_bars - 1] + take, "None", i, number_bars - i, "BUY"
    return 0, "", -1, -1, ""


def main(curr: Currency, start: datetime, end: datetime, probability: float, number_bars: int, history_min: int,
         enter: float):
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
            curr=curr, greed=greed, time=current_time, number_bars=number_bars, enter=enter)

        if d >= 0:
            yield [current_time.replace(tzinfo=None), res, state, len(greed), d, open_d, sb]
