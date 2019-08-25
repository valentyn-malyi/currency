import numpy
import sqlite3
import os
from datetime import datetime, timedelta
from collections import deque
from typing import Iterator
from pytz import timezone


class Period:

    def __init__(self, number_bars):
        self.number_bars = number_bars

    delta: timedelta
    period: str

    @staticmethod
    def utc(time: datetime):
        return time.replace(tzinfo=timezone('UTC'))


class Daily(Period):
    period = "Daily"
    delta = timedelta(days=1)

    @staticmethod
    def utc(time: datetime):
        return time.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=timezone('UTC'))


class H8(Period):
    period = "H8"
    delta = timedelta(hours=8)


class H4(Period):
    period = "H4"
    delta = timedelta(hours=4)


class Bar:
    def __init__(self, time: datetime, close: float, high: float, low: float):
        self.close = close
        self.time = time
        self.high = high
        self.low = low

    def __repr__(self):
        return f"{self.time.timestamp()}|{self.time}|{self.close}"


class Similar(Bar):

    def __init__(self, bar: Bar, corrcoef: float, n: int):
        super().__init__(time=bar.time, high=bar.high, low=bar.low, close=bar.close)
        self.corrcoef = corrcoef
        self.corrcoef_index = corrcoef >= 0
        self.abs = abs(corrcoef)
        self.n = n

    def __repr__(self):
        return f"{self.time.timestamp()}|{self.time}|{self.close}"


class Currency:

    def __init__(self, period: Period, first: str = "usd", second: str = "usd"):
        self.name = f"{first}{second}"
        self.oanda = f"{first.upper()}_{second.upper()}"
        self.period = period
        home = os.path.join(os.path.dirname(__file__), "..")
        self.conn = sqlite3.connect(os.path.join(home, "schemas", "history", "history.db"))
        self.cursor = self.conn.cursor()
        self.table = "currency_" + self.name + period.period

    def close(self):
        self.cursor.close()
        self.conn.close()

    def left(self, time: datetime, n: int) -> Iterator[Bar]:
        # noinspection SqlResolve
        self.cursor.execute(
            "SELECT * FROM (SELECT * FROM {table} WHERE t < {t} ORDER BY -t LIMIT {n}) AS s "
            "ORDER BY s.t".format(table=self.table, t=time.timestamp(), n=n))
        for select in self.cursor.fetchall():
            yield Bar(time=datetime.utcfromtimestamp(select[0]).replace(tzinfo=timezone('UTC')), close=select[3],
                      high=select[1], low=select[2])

    def right(self, time: datetime, n: int) -> Iterator[Bar]:
        # noinspection SqlResolve
        self.cursor.execute(
            "select * from {table} where t >= {t} order by t limit {n}".format(
                table=self.table, t=time.timestamp(), n=n))
        for select in self.cursor.fetchall():
            yield Bar(time=datetime.utcfromtimestamp(select[0]).replace(tzinfo=timezone('UTC')), close=select[3],
                      high=select[1], low=select[2])

    def slices(self, array: numpy.array, time: datetime, probability: float) -> Iterator[Similar]:
        n = len(array)
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

    def profit(self, similar: Similar) -> numpy.array:
        close = []
        first = next(self.left(time=similar.time, n=1)).close
        atr = self.atr(similar.time)
        if similar.corrcoef_index:
            for select in self.right(time=similar.time, n=similar.n):
                close.append((select.close - first) / atr)
        else:
            for select in self.right(time=similar.time, n=similar.n):
                close.append((first - select.close) / atr)
        return numpy.array(close)

    def atr(self, time) -> float:
        s = 0
        for select in self.left(time=time, n=5):
            s += select.high - select.low
        return s / 5

    def get_high_low(self, time, n) -> (numpy.array, numpy.array, numpy.array):
        atr = self.atr(time=time)
        close = []
        high = []
        low = []
        first = next(self.left(time=time, n=1)).close
        for select in self.right(time=time, n=n):
            close.append(select.close - first)
            high.append(select.high - first)
            low.append(select.low - first)
        return numpy.array(close) / atr, numpy.array(high) / atr, numpy.array(low) / atr

    def mean_and_sd(self, array: numpy.array, time, probability, history_min) -> (bool, numpy.array, numpy.array, int):
        list_profits = []
        len_similars = 0
        for similar in self.slices(array=array, time=time, probability=probability):
            list_profits.append(self.profit(similar=similar))
            len_similars += 1
        if history_min <= len(list_profits):
            mean = numpy.mean(list_profits, axis=0)
            sd = numpy.std(list_profits, axis=0)
            return True, mean, abs(mean) / sd, len_similars
        return False, numpy.array([]), numpy.array([]), len_similars
