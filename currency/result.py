from currency.currency import Currency
from datetime import datetime
import numpy
from typing import Generator, Tuple


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


def main(curr: Currency, start: datetime, end: datetime, probability: float, number_bars: int, history_min: int,
         stop: int, take: int):
    year = None
    for current_bar in curr.right(time=start, n=999999999):
        current_time = current_bar.time
        if current_time.year != year:
            print(current_time.year)
            year = current_time.year
        if current_time >= end:
            break
        array = []
        for bar in curr.left(time=current_time, n=number_bars):
            array.append(bar.close)
        array = numpy.array(array)
        index, mean, sd, len_similars = curr.mean_and_sd(
            array=array, time=current_time, history_min=history_min, probability=probability)
        if index:
            for res, state, d in result(curr=curr, mean=mean, time=current_time, take=take, stop=stop):
                yield [current_time.replace(tzinfo=None), res, d, state, len_similars, sd[d], abs(mean[d])]
