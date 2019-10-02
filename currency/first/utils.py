import random
import json
import os
import sqlite3
import numpy
from datetime import datetime
from typing import List, Iterator, Union
from currency.utils import Currency, Daily, H4, H8, TimeInterval

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))


def null(x):
    if isinstance(x, str):
        return "null" if x is None else f"'{x}'"
    else:
        return "null" if x is None else x


class Args:
    skip = 0


class First:
    connection = sqlite3.connect(os.path.join(HOME, "schemas", "history", "history.db"))
    cursor = connection.cursor()

    class Settings:

        def __init__(self, probability: float, number_bars: int, history_min: int, stop: float, take: float, mean: float, sd: float,
                     skip: int = Args.skip):
            self.probability = probability
            self.number_bars = number_bars
            self.history_min = history_min
            self.stop = stop
            self.take = take
            self.skip = skip
            self.mean = mean
            self.sd = sd

        @classmethod
        def init_from_dict(cls, d: dict) -> "First.Settings":
            probability = d["probability"]
            number_bars = d["number_bars"]
            history_min = d["history_min"]
            stop = d["stop"]
            take = d["take"]
            mean = d["mean"]
            sd = d["sd"]
            skip = d.get("skip", Args.skip)

            return cls(probability=probability, number_bars=number_bars, history_min=history_min, stop=stop, take=take, mean=mean,
                       sd=sd, skip=skip)

    class Config:
        config_name = "first.json"
        context_keys = "contexts"
        current_context_key = "current_context"

        def __init__(self, curency: List[Currency], settings: "First.Settings"):
            self.curency = curency
            self.settings = settings

        @classmethod
        def init_from_file(cls) -> "First.Config":
            config = json.load(open(os.path.join(HOME, cls.config_name)))
            current_name = config[cls.current_context_key]
            context = config[cls.context_keys][current_name]

            settings = First.Settings.init_from_dict(context)
            period_time = context["period"]["time"]

            if period_time == "Daily":
                period = Daily(number_bars=context["period"]["n"])
            elif period_time == "H4":
                period = H4(number_bars=context["period"]["n"])
            elif period_time == "H8":
                period = H8(number_bars=context["period"]["n"])
            else:
                raise Exception(f"No find {period_time} period time ")

            curency = []
            for cur in context["currs"]:
                curency.append(Currency(period=period, **cur))
            return cls(
                curency=curency, settings=settings)

    class Trade:
        def __init__(self, state: str = None, oanda: str = None, gain: str = None, c: int = None):
            self.state = state
            self.oanda = oanda
            self.gain = gain
            self.c = c

        def update(self, state: str, gain: float, c: int):
            self.state = state
            self.gain = gain
            self.c = c

    def __init__(self, time: datetime, currency: Currency, settings: Settings):

        self.currency = currency
        self.time = currency.period.utc(time)
        self.settings = settings
        self.trade = self.Trade()
        self.gain_mean: Union[float, None] = None
        self.n: Union[int, None] = None
        self.direction: Union[str, None] = None

        array = []
        for bar in currency.left(time=time, n=settings.number_bars):
            array.append(bar.close)
        self.array = numpy.array(array)

        self.mean, self.sd, self.history = currency.mean_and_sd(array=array, time=time, probability=settings.probability)
        self.mean = -self.mean

        self.good_days = numpy.where(numpy.logical_and(abs(self.mean) > settings.mean, self.sd > settings.sd))[0]

        if self.history >= self.settings.history_min and self.good_days.size:
            self.n = self.good_days[-1]
            self.gain_mean = self.mean[self.n]
            self.direction = "buy" if self.gain_mean > 0 else "sell"

    def __repr__(self):
        return f"{self.time}|{self.time.timestamp()}|{self.currency.name}|{self.n}|{self.gain_mean}|{self.direction}" \
               f"\n{self.trade.gain},{self.trade.state},{self.trade.c}"

    def save_first_time(self):
        if self.n is not None:
            sql = f"INSERT OR IGNORE into currency_first(t,currency,str_datetime,n,gain_mean,direction,history) values " \
                  f"(" \
                  f"{self.time.timestamp()}," \
                  f"'{self.currency.first}|{self.currency.second}'," \
                  f"'{str(self.time)}'," \
                  f"{self.n}," \
                  f"{self.gain_mean}," \
                  f"'{self.direction}'," \
                  f"{self.history}" \
                  f")"
            self.cursor.execute(sql)
            self.connection.commit()

    @classmethod
    def truncate_table(cls):
        # noinspection SqlResolve
        sql = "DELETE FROM currency_first where id is not null "
        cls.cursor.execute(sql)
        cls.connection.commit()

    @classmethod
    def get_from_table(cls, currency: Currency, settings: Settings) -> Iterator["First"]:
        sql = f"SELECT t,oanda,state FROM currency_first where state is null " \
              f"and currency='{currency.first}|{currency.second}'"
        cls.cursor.execute(sql)
        for line in cls.cursor.fetchall():
            time = currency.period.utc(datetime.utcfromtimestamp(line[0]))
            first = cls(time=time, currency=currency, settings=settings)
            first.trade.oanda = line[1]
            first.trade.state = line[2]
            yield first

    def enter_close(self) -> float:
        return next(self.currency.left(time=self.time, n=1)).close

    def atr(self) -> float:
        return self.currency.atr(self.time)

    def is_close(self, time: datetime):
        if self.currency.period.get_working_bars(start=self.time, end=time) > self.n:
            return True
        else:
            return False

    def result(self):
        if self.n is not None:
            close, high, low = self.currency.get_high_low(time=self.time, n=self.n + 1)
            if self.gain_mean > 0:
                for i in range(self.n):
                    if low[i] < self.mean[i] - self.settings.stop:
                        self.trade.update(gain=self.mean[i] - self.settings.stop, c=i, state="STOP")
                        break
                    if high[i] > self.mean[i] + self.settings.take:
                        self.trade.update(gain=self.mean[i] + self.settings.take, c=i, state="TAKE")
                        break
                else:
                    self.trade.update(gain=close[self.n], c=self.n, state="CLOSE")
            else:
                for i in range(self.n):
                    if high[i] > self.mean[i] + self.settings.stop:
                        self.trade.update(gain=-self.mean[i] - self.settings.stop, c=i, state="STOP")
                        break
                    if low[i] < self.mean[i] - self.settings.take:
                        self.trade.update(gain=-self.mean[i] + self.settings.take, c=i, state="TAKE")
                        break
                else:
                    self.trade.update(gain=-close[self.n], c=self.n, state="CLOSE")

    def save(self):
        if self.n is not None:
            sql = f"UPDATE currency_first set " \
                  f"gain={null(self.trade.gain)}," \
                  f"state={null(self.trade.state)}," \
                  f"c={null(self.trade.c)}," \
                  f"oanda={null(self.trade.oanda)} " \
                  f"where t={self.time.timestamp()} and currency='{self.currency.first}|{self.currency.second}'"
            self.cursor.execute(sql)
            self.connection.commit()


def run_history(curency: Currency, time_interval: TimeInterval, first_config: First.Config) -> Iterator[First]:
    time = time_interval.start
    while time < time_interval.end:
        time += curency.period.delta
        if time.weekday() in [5, 6]:
            continue
        if random.random() < first_config.settings.skip:
            continue
        first = First(time=time, currency=curency, settings=first_config.settings)
        if first.n is not None:
            yield first

# from datetime import timedelta
#
# c = First.Config.init_from_file()
# cur = c.curency[0]
#
# First.truncate_table()
# for i in range(50):
#     t = datetime.now() - timedelta(days=300 + i)
#     t = cur.period.utc(t)
#     if t.weekday() in [5, 6]:
#         continue
#
#     first = First(time=t, currency=cur, settings=c.settings)
#     print(first.n)
#     print(first.history)
#     print(first.result())
#     first.save_first_time()
#
# for ii in First.get_from_table(currency=cur, settings=c.settings):
#     print(ii)
