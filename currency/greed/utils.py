import bisect
import json
import os
import sqlite3
import numpy
from datetime import datetime
from typing import List, Iterator
from currency.utils import Currency, Daily, H4, H8, TimeInterval
from typing import Callable

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))


def null(x):
    if isinstance(x, str):
        return "null" if x is None else f"'{x}'"
    else:
        return "null" if x is None else x


def destrib(a: numpy.array, x: float) -> float:
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


class Greed:
    connection = sqlite3.connect(os.path.join(HOME, "history.db"))
    cursor = connection.cursor()

    class Settings:

        def __init__(self, probability: float, number_bars: int, history_min: int, enter: float, stop_coef: float, skip_open: int, skip_close: int):
            self.probability = probability
            self.number_bars = number_bars
            self.history_min = history_min
            self.enter = enter
            self.stop_coef = stop_coef
            self.skip_open = skip_open
            self.skip_close = skip_close

        @classmethod
        def init_from_dict(cls, d: dict) -> "Greed.Settings":
            probability = d["probability"]
            number_bars = d["number_bars"]
            history_min = d["history_min"]
            enter = d["enter"]
            stop_coef = d["stop_coef"]
            skip_open = d["skip_open"]
            skip_close = d.get("skip_close")

            return cls(probability=probability, number_bars=number_bars, history_min=history_min, enter=enter, stop_coef=stop_coef,
                       skip_open=skip_open, skip_close=skip_close)

    class Config:
        config_name = "greed.json"
        context_keys = "contexts"
        current_context_key = "current_context"

        def __init__(self, curency: List[Currency], settings: "Greed.Settings"):
            self.curency = curency
            self.settings = settings

        @classmethod
        def init_from_file(cls) -> "Greed.Config":
            config = json.load(open(os.path.join(HOME, cls.config_name)))
            current_name = config[cls.current_context_key]
            context = config[cls.context_keys][current_name]

            settings = Greed.Settings.init_from_dict(context)

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
                curency=curency, settings=settings)

    class Trade:
        def __init__(self, last_update: datetime, gain: float = None, state: str = None, direction: str = None, o: int = None, c: int = None,
                     oanda: int = None,
                     right_bar: int = 0):
            self.last_update = last_update
            self.gain = gain
            self.state = state
            self.direction = direction
            self.o = o
            self.c = c
            self.oanda = oanda
            self.right_bar = right_bar

        def is_open(self) -> bool:
            return self.o is not None

        def is_close(self) -> bool:
            return self.is_open() and self.c is not None

        def is_status(self) -> bool:
            return self.state is not None

        def __repr__(self):
            return f"{self.right_bar}|{self.is_open()}|{self.is_close()}|{self.gain}|{self.state}|{self.o}|{self.c}"

    def __init__(self, time: datetime, currency: Currency, settings: Settings):

        self.currency = currency
        self.time = currency.period.utc(time)
        self.settings = settings
        self.trade = self.Trade(last_update=self.time)

        left = []
        for bar in currency.left(time=self.time, n=settings.number_bars):
            left.append(bar.close)
        self.left = numpy.array(left)
        greed = []

        for sl in currency.slices(array=self.left, time=self.time, probability=settings.probability):
            close, _, _ = currency.get_high_low(time=sl.time, n=settings.number_bars)
            greed.append(close)

        self.greed = numpy.array(greed)
        self.len_greed = len(self.greed)

        self.close, self.high, self.low = currency.get_high_low(time=self.time, n=settings.number_bars)

    def __repr__(self):
        return f"{self.time}|{self.time.timestamp()}|{self.currency.name}|{len(self.greed)}\n{self.trade}"

    def last_price(self) -> float:
        return list(self.currency.right(self.time, self.trade.right_bar))[self.trade.right_bar - 1].close

    def atr(self) -> float:
        return self.currency.atr(self.time)

    def save(self, end: datetime):
        end = self.currency.period.utc(end)
        if end > self.trade.last_update:
            sql = f"UPDATE currency_greed set " \
                  f"gain={null(self.trade.gain)}," \
                  f"state={null(self.trade.state)}," \
                  f"direction={null(self.trade.direction)}," \
                  f"o={null(self.trade.o)}," \
                  f"c={null(self.trade.c)}," \
                  f"oanda={null(self.trade.oanda)}," \
                  f"last_update={end.timestamp()}," \
                  f"str_last_update='{str(end)}' " \
                  f"where t={self.time.timestamp()} and currency='{self.currency.first}|{self.currency.second}'"
            self.cursor.execute(sql)
            self.connection.commit()

    def save_first_time(self):
        sql = f"INSERT OR REPLACE into currency_greed(t,currency,history,str_datetime,last_update,str_last_update) values " \
              f"(" \
              f"{self.time.timestamp()}," \
              f"'{self.currency.first}|{self.currency.second}'," \
              f"{self.len_greed}," \
              f"'{str(self.time)}'," \
              f"{self.time.timestamp()}," \
              f"'{str(self.time)}'" \
              f")"
        self.cursor.execute(sql)
        self.connection.commit()

    @classmethod
    def truncate_table(cls):
        # noinspection SqlResolve
        sql = "DELETE FROM currency_greed where id is not null "
        cls.cursor.execute(sql)
        cls.connection.commit()

    @classmethod
    def get_greed_from_table(cls, currency: Currency, settings: Settings) -> Iterator["Greed"]:
        sql = f"SELECT t,currency,gain,state,direction,o,c,last_update,oanda FROM currency_greed where state is null " \
              f"and currency='{currency.first}|{currency.second}'"
        cls.cursor.execute(sql)
        for line in cls.cursor.fetchall():
            time = currency.period.utc(datetime.utcfromtimestamp(line[0]))
            greed = cls(time=time, currency=currency, settings=settings)
            greed.trade.gain = line[2]
            greed.trade.state = line[3]
            greed.trade.direction = line[4]
            greed.trade.o = line[5]
            greed.trade.c = line[6]
            greed.trade.last_update = currency.period.utc(datetime.utcfromtimestamp(line[7]))
            greed.trade.right_bar = currency.period.get_working_bars(start=time, end=greed.trade.last_update) - 1
            greed.trade.oanda = line[8]
            yield greed

    def check_open(self):
        if not self.trade.is_status() and not self.trade.is_open() and self.trade.right_bar > 0:
            n = self.trade.right_bar - 1
            greed_day = self.greed[:, n]
            greed_day.sort()
            if destrib(a=greed_day, x=self.close[n]) > 1 - self.settings.enter and self.close[n] > 0:
                self.trade.o = n
                self.trade.direction = "sell"
            elif destrib(a=greed_day, x=self.close[n]) < self.settings.enter and self.close[n] < 0:
                self.trade.o = n
                self.trade.direction = "buy"

    def day_enter(self) -> int:
        return self.trade.o + self.settings.skip_open

    def check_skip(self) -> bool:
        return self.day_enter() < self.trade.right_bar

    def day_enter_close(self) -> float:
        return self.close[self.day_enter()]

    def close_trade(self, y_state: str, n_state: str, gain: Callable):
        if self.check_skip():
            self.trade.state = y_state
            self.trade.gain = gain(None)
            self.trade.c = self.trade.right_bar
        else:
            self.trade.state = n_state

    def check_end(self):
        if self.trade.right_bar == self.settings.number_bars - 1:
            if self.trade.is_open():
                self.trade.c = self.trade.right_bar
                if self.trade.gain is None:
                    self.trade.state = "SKIP_END_BARS"
                else:
                    self.trade.state = "CLOSE_END_BARS"
            else:
                self.trade.state = "NO_POINT"

    def get_gain(self):
        if not self.trade.is_status() and self.trade.is_open():
            n = self.trade.right_bar
            stop = (self.settings.stop_coef + 1) * self.close[self.trade.o]

            if self.trade.direction == "sell":
                if self.high[n] > stop:
                    self.close_trade("STOP", "STOP_SKIP", lambda x: self.day_enter_close() - stop)

                elif self.low[n] < 0:
                    self.close_trade("TAKE", "TAKE_SKIP", lambda x: self.day_enter_close())

                elif n - self.trade.o >= self.settings.skip_close:
                    self.trade.state = "CLOSE"
                    self.trade.gain = self.day_enter_close() - self.close[n]
                    self.trade.c = n

                elif self.check_skip():
                    self.trade.gain = self.day_enter_close() - self.close[n]

            if self.trade.direction == "buy":
                if self.low[n] < stop:
                    self.close_trade("STOP", "STOP_SKIP", lambda x: stop - self.day_enter_close())

                elif self.high[n] > 0:
                    self.close_trade("TAKE", "TAKE_SKIP", lambda x: -self.day_enter_close())

                elif n - self.trade.o >= self.settings.skip_close:
                    self.trade.state = "CLOSE"
                    self.trade.gain = self.close[n] - self.day_enter_close()
                    self.trade.c = n

                elif self.check_skip():
                    self.trade.gain = self.close[n] - self.day_enter_close()

    def update_right_bar(self, end: datetime):
        end = self.currency.period.utc(end)
        if end < self.time:
            raise ValueError(f"end < self.time\nstart = {self.time}\nend = {end}")
        self.trade.right_bar = self.currency.period.get_working_bars(start=self.time, end=end)


def run_history(time_interval: TimeInterval, curency: Currency, greed_config: Greed.Config) -> Iterator[Greed]:
    time = time_interval.start
    while time < time_interval.end:
        time += curency.period.delta
        if time.weekday() in [5, 6]:
            continue
        greed = Greed(time=time, currency=curency, settings=greed_config.settings)
        if greed.len_greed < greed_config.settings.history_min:
            continue
        while not greed.trade.is_status():
            greed.get_gain()
            greed.trade.right_bar += 1
            greed.check_open()
            greed.check_end()
        yield greed


def insert_greed_table(last_for=70):
    Greed.truncate_table()
    greed_config = Greed.Config.init_from_file()
    for curency in greed_config.curency:
        end = curency.period.utc(datetime.now()) - curency.period.delta
        time = end - curency.period.delta * last_for
        while time < end:
            time += curency.period.delta
            if time.weekday() in [5, 6]:
                continue
            for greed in Greed.get_greed_from_table(curency, settings=greed_config.settings):
                greed.get_gain()
                greed.update_right_bar(end=time)
                greed.check_open()
                greed.check_end()
                greed.save(end=time)
            greed = Greed(time=time, currency=curency, settings=greed_config.settings)
            print(greed)
            if greed.len_greed >= greed_config.settings.history_min:
                greed.save_first_time()

# insert_greed_table(10)
