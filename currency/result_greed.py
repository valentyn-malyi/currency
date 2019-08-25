import json
import numpy
import bisect
import os
import sqlite3

from pytz import timezone
from currency.utils import Currency, Daily, H4, H8
from datetime import datetime
from typing import Tuple, Union, List


# import matplotlib.pyplot as plt

class Config:
    config_name = "greed.json"
    context_keys = "contexts"
    current_context_key = "current_context"

    def __init__(
            self, curency: List[Currency], start: datetime, end: datetime, probability: float, number_bars: int,
            history_min: int, enter: float, stop_coef: float, skip_open: int, skip_close: int):
        self.curency = curency
        self.start = start
        self.end = end
        self.probability = probability
        self.number_bars = number_bars
        self.history_min = history_min
        self.enter = enter
        self.stop_coef = stop_coef
        self.skip_open = skip_open
        self.skip_close = skip_close

    @classmethod
    def init_from_file(cls, path="."):
        config = json.load(open(os.path.join(path, cls.config_name)))
        current_name = config[cls.current_context_key]
        context = config[cls.context_keys][current_name]
        start = datetime(year=context["start"]["year"], month=context["start"]["month"], day=context["start"]["day"],
                         tzinfo=timezone('UTC'))
        end = datetime(year=context["end"]["year"], month=context["end"]["month"], day=context["end"]["day"],
                       tzinfo=timezone('UTC'))
        probability = context["probability"]
        number_bars = context["number_bars"]
        history_min = context["history_min"]
        enter = context["enter"]
        stop_coef = context["stop_coef"]
        skip_open = context["skip_open"]
        skip_close = context["skip_close"]
        if skip_close is None:
            skip_close = skip_close

        period_time = context["period"]["time"]
        period = None
        if period_time == "Daily":
            period = Daily(number_bars=context["period"]["n"])
        elif period_time == "H4":
            period = H4(number_bars=context["period"]["n"])
        elif period_time == "H8":
            period = H8(number_bars=context["period"]["n"])

        curency = []
        for cur in context["currs"]:
            curency.append(Currency(period=period, **cur))
        return cls(
            curency=curency, start=start, end=end, probability=probability, number_bars=number_bars,
            history_min=history_min, enter=enter, stop_coef=stop_coef, skip_open=skip_open, skip_close=skip_close)


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
                if high[i + skip_day_i] > stop:
                    return 0, "SKIP_DAY", i, skip_day_i, "SELL"
            offer = close[i + skip_open - 1]
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
            offer = close[i + skip_open - 1]
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


def run_history(curr: Currency, start: datetime, end: datetime, probability: float, number_bars: int, history_min: int,
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
        for sl in curr.slices(array=array, time=current_time, probability=probability):
            close, _, _ = curr.get_high_low(time=sl.time, n=number_bars)
            greed.append(close)
        greed = numpy.array(greed)
        if len(greed) < history_min:
            continue
        res, state, d, open_d, sb = result(
            curr=curr, greed=greed, time=current_time, number_bars=number_bars, enter=enter, stop_coef=stop_coef,
            skip_open=skip_open, skip_close=skip_close)

        if d is not None:
            yield [current_time.replace(tzinfo=None), res, state, len(greed), d, open_d, sb]


def insert_today(time: datetime):
    home = os.path.join(os.path.dirname(__file__), "..")
    c = Config.init_from_file(path=home)

    for curr in c.curency:
        conn = sqlite3.connect(os.path.join(home, "schemas", "history", "history.db"))
        cursor = conn.cursor()
        current_time = curr.period.utc(time)
        array = []
        for bar in curr.left(time=current_time, n=c.number_bars):
            array.append(bar.close)

        array = numpy.array(array)
        greed = len(list(curr.slices(array=array, time=current_time, probability=c.probability)))
        sql = f"INSERT OR REPLACE " \
              f"into currency_greed(t,currency,history) " \
              f"values ({current_time.timestamp()}, '{curr.name}', {greed})"
        cursor.execute(sql)
        conn.commit()


if __name__ == '__main__':
    t = datetime.utcnow()
    # insert_today(time=t)

