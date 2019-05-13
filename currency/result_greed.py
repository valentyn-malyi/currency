from currency.currency import Currency
from datetime import datetime
import numpy
import bisect
from typing import Generator, Tuple, List
import matplotlib.pyplot as plt


def destrib(a: numpy.ndarray, x:float):
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


def result(curr: Currency, greed: List[numpy.array], time: datetime, number_bars: int,
           enter: float) -> Generator[Tuple[float, str, int], None, None]:
    close, high, low = curr.get_high_low(time=time, n=number_bars)
    for d in range(number_bars):
        g = greed[:,d]
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


def main(curr: Currency, start: datetime, end: datetime, probability: float, number_bars: int, history_min: int,
         stop: int, take: int):
    for current_bar in curr.right(time=start, n=999999999):
        current_time = current_bar.time
        print(current_time)
        if current_time >= end:
            break
        array = []
        for bar in curr.left(time=current_time, n=number_bars):
            array.append(bar.close)
        array = numpy.array(array)
        greed = [0]
        for slice in curr.slices(array=array, time=current_time, probability=probability):
            close, _, _ = curr.get_high_low(time=slice.time, n=number_bars)
            greed.append(close)
            greed.append(-close)
        print(greed)
        for i in greed:
            plt.plot(i)
        plt.show()
        plt.clf()
        # index, mean, sd, len_similars = curr.mean_and_sd(
        #     array=array, time=current_time, history_min=history_min, probability=probability)
        # if index:
        #     for res, state, d in result(curr=curr, mean=mean, time=current_time, take=take, stop=stop):
        #         yield [current_time.replace(tzinfo=None), res, d, state, len_similars, sd[d], abs(mean[d])]
