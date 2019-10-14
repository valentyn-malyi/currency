import numpy
import sqlite3
import os
import json
from datetime import datetime, timedelta
from collections import deque
from typing import Iterator, Tuple
from pytz import timezone

HOME = os.path.join(os.path.join(os.path.dirname(__file__), ".."))


class Period:

    def __init__(self, number_bars):
        self.number_bars = number_bars

    delta: timedelta
    period: str
    atr: int

    @staticmethod
    def utc(time: datetime) -> datetime:
        return time.replace(tzinfo=timezone('UTC'))

    @staticmethod
    def get_working_bars(start: datetime, end: datetime) -> int:
        return 0


class TimeInterval:
    config_name = "time_interval.json"
    context_keys = "contexts"
    current_context_key = "current_context"

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    @classmethod
    def init_from_file(cls) -> "TimeInterval":
        config = json.load(open(os.path.join(HOME, cls.config_name)))
        current_name = config[cls.current_context_key]
        context = config[cls.context_keys][current_name]
        start = datetime(year=context["start"]["year"], month=context["start"]["month"], day=context["start"]["day"],
                         tzinfo=timezone('UTC'))
        end = datetime(year=context["end"]["year"], month=context["end"]["month"], day=context["end"]["day"],
                       tzinfo=timezone('UTC'))

        return cls(start=start, end=end)


class Daily(Period):
    period = "Daily"
    delta = timedelta(days=1)
    atr = 5

    @staticmethod
    def utc(time: datetime) -> datetime:
        return time.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=timezone('UTC'))

    @staticmethod
    def get_working_bars(start: datetime, end: datetime) -> int:
        if start > end:
            return -1
        sw, ew = start.weekday(), end.weekday()
        s1 = start - timedelta(days=sw)
        e1 = end - timedelta(days=ew)
        s = (e1 - s1).days // 7 * 5
        t = ew - sw
        if sw == 6:
            t += 1
        if ew == 6:
            t -= 1
        return s + t


class H8(Period):
    period = "H8"
    delta = timedelta(hours=8)
    atr = 15


class H4(Period):
    atr = 30
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


class Currency:

    def __init__(self, period: Period, first: str = "usd", second: str = "usd"):
        self.first = first
        self.second = second
        self.name = f"{first}{second}"
        self.oanda = f"{first.upper()}_{second.upper()}"
        self.decode = f"{first.upper()}|{second.upper()}"
        self.period = period
        home = os.path.join(os.path.dirname(__file__), "..")
        self.conn = sqlite3.connect(os.path.join(home, "history.db"))
        self.cursor = self.conn.cursor()
        self.table = "currency_" + self.name + period.period

    def __repr__(self):
        return f"{self.name}"

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

    def slices(self, array: numpy.array, time: datetime, probability: float, abs_factor: bool = True) -> Iterator[Similar]:
        n = len(array)
        delta = self.period.delta * n
        double_delta = delta * 2
        deq = deque(maxlen=n)
        last_time = datetime.min
        last_time = last_time.replace(tzinfo=timezone('UTC'))
        for bar in self.left(time=time - double_delta, n=self.period.number_bars):
            deq.append(bar.close)
            if len(deq) < n or bar.time - last_time < delta:
                continue
            corrcoef = numpy.corrcoef(array, deq)[0, 1]

            if abs_factor:
                if abs(corrcoef) > probability:
                    last_time = bar.time
                    yield Similar(bar=bar, corrcoef=corrcoef, n=n)
            else:
                if corrcoef > probability:
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
        for bar in self.left(time=time, n=self.period.atr):
            s += bar.high - bar.low
        return s / self.period.atr

    def get_high_low(self, time, n) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
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

    def mean_and_sd(self, array: numpy.array, time: datetime, probability: float) -> Tuple[numpy.ndarray, numpy.ndarray, int]:
        list_profits = []
        len_similars = 0
        for similar in self.slices(array=array, time=time, probability=probability):
            list_profits.append(self.profit(similar=similar))
            len_similars += 1
        if len(list_profits) >= 2:
            mean = numpy.mean(list_profits, axis=0)
            sd = numpy.std(list_profits, axis=0)
            return mean, abs(mean) / sd, len_similars
        else:
            return numpy.array([]), numpy.array([]), len_similars
