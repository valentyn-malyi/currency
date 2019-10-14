import json
import os
import sqlite3
import numpy
from datetime import datetime
from typing import List, Iterator, Union
from currency.utils import Currency, Daily, H4, H8, Period, TimeInterval

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))


def null(x):
    if isinstance(x, str):
        return "null" if x is None else f"'{x}'"
    else:
        return "null" if x is None else x


class Args:
    skip = 0


class CurencyPair:
    def __init__(self, currency_main: Currency, currencies: List[Currency]):
        self.currencies = currencies
        self.currency_main = currency_main

    def __repr__(self):
        return repr(self.currency_main) + repr(self.currencies)

    @classmethod
    def init_from_dict(cls, d: dict, period: Period) -> "CurencyPair":
        currencies = []
        for cur in d.pop("currs"):
            currencies.append(Currency(period=period, **cur))
        currency_main = Currency(period=period, **d)
        return cls(currency_main=currency_main, currencies=currencies)

    def encode(self):
        currencies_str = [curr.decode for curr in self.currencies]
        currencies_str.sort()
        currencies = ",".join(currencies_str)
        return f"{self.currency_main.decode}_{currencies}"


class Third:
    connection = sqlite3.connect(os.path.join(HOME, "history.db"))
    cursor = connection.cursor()

    class Settings:

        def __init__(self, probability: float, number_bars: int, stop: float, take: float, step_coef: float):
            self.probability = probability
            self.number_bars = number_bars
            self.stop = stop
            self.take = take
            self.step_coef = step_coef

        @classmethod
        def init_from_dict(cls, d: dict) -> "Third.Settings":
            probability = d["probability"]
            number_bars = d["number_bars"]
            stop = d["stop"]
            take = d["take"]
            step_coef = d["step_coef"]

            return cls(probability=probability, number_bars=number_bars, stop=stop, take=take, step_coef=step_coef)

    class Config:
        config_name = "third.json"
        context_keys = "contexts"
        current_context_key = "current_context"

        def __init__(self, currency_pairs: List[CurencyPair], settings: "Third.Settings"):
            self.settings = settings
            self.currency_pairs = currency_pairs

        @classmethod
        def init_from_file(cls) -> "Third.Config":
            config = json.load(open(os.path.join(HOME, cls.config_name)))
            current_name = config[cls.current_context_key]
            context = config[cls.context_keys][current_name]

            settings = Third.Settings.init_from_dict(context)
            period_time = context["period"]["time"]

            if period_time == "Daily":
                period = Daily(number_bars=context["period"]["n"])
            elif period_time == "H4":
                period = H4(number_bars=context["period"]["n"])
            elif period_time == "H8":
                period = H8(number_bars=context["period"]["n"])
            else:
                raise Exception(f"No find {period_time} period time ")

            currency_pairs = []

            for cur in context["currs"]:
                currency_pairs.append(CurencyPair.init_from_dict(d=cur, period=period))
            return cls(currency_pairs=currency_pairs, settings=settings)

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

    def __init__(self, time: datetime, currency_pair: CurencyPair, settings: Settings):
        self.currency_pair = currency_pair
        self.time = self.currency_pair.currency_main.period.utc(time)
        self.settings = settings
        self.trade = self.Trade()
        self.gain_mean: Union[float, None] = None
        self.n: Union[int, None] = None
        self.direction: Union[str, None] = None
        self.array_dict = dict()
        self.situation_time: Union[datetime, None] = None
        self.situations = dict()
        self.mean: Union[numpy.ndarray, None] = None
        self.close: Union[numpy.ndarray, None] = None
        self.high: Union[numpy.ndarray, None] = None
        self.low: Union[numpy.ndarray, None] = None
        self.coef = 0

        for currency in [self.currency_pair.currency_main] + self.currency_pair.currencies:
            array1 = []
            for bar in currency.left(time=self.time, n=self.settings.number_bars):
                array1.append(bar.close)
            self.array_dict[currency] = numpy.array(array1)

        for slice_main in self.currency_pair.currency_main.slices(
                array=self.array_dict[self.currency_pair.currency_main], time=self.time, probability=self.settings.probability, abs_factor=False):
            self.situations[slice_main.time] = slice_main.abs

        for currency in currency_pair.currencies:
            new_situations = dict()

            for similar in currency.slices(array=self.array_dict[currency], time=self.time, probability=self.settings.probability, abs_factor=False):
                new_situations[similar.time] = similar.abs

            for slice_time, slice_abs in self.situations.copy().items():

                if slice_time in new_situations:
                    self.situations[slice_time] = self.situations[slice_time] * slice_abs
                else:
                    self.situations.pop(slice_time)

            if not self.situations:
                break

        if self.situations:
            slice_abs_max = float("-inf")
            for slice_time, slice_abs in self.situations.items():
                if slice_abs > slice_abs_max:
                    self.situation_time = slice_time
                    slice_abs_max = slice_abs
            self.mean, _, _ = self.currency_pair.currency_main.get_high_low(time=self.situation_time, n=self.settings.number_bars)

            for n, element in enumerate(self.mean):
                if abs(element) > self.settings.step_coef * (n + 1):
                    self.n = n
                    self.coef += 1
                    self.gain_mean = element

            if self.n is not None:
                self.direction = "buy" if self.gain_mean > 0 else "sell"
                self.close, self.high, self.low = self.currency_pair.currency_main.get_high_low(time=self.time, n=self.n + 1)

    def __repr__(self):
        return f"{self.time}|{self.time.timestamp()}|{self.currency_pair.currency_main.name}|{self.n}|{self.gain_mean}|{self.direction}" \
               f"\n{self.trade.gain},{self.trade.state},{self.trade.c}"

    def save_first_time(self):
        if self.n is not None:
            sql = f"INSERT OR IGNORE into currency_third(t,currency_pair,str_datetime,n,gain_mean,direction) values " \
                  f"(" \
                  f"{self.time.timestamp()}," \
                  f"'{self.currency_pair.encode()}'," \
                  f"'{str(self.time)}'," \
                  f"{self.n}," \
                  f"{self.gain_mean}," \
                  f"'{self.direction}'" \
                  f")"
            self.cursor.execute(sql)
            self.connection.commit()

    @classmethod
    def truncate_table(cls):
        # noinspection SqlResolve
        sql = "DELETE FROM currency_third where id is not null "
        cls.cursor.execute(sql)
        cls.connection.commit()

    @classmethod
    def get_from_table(cls, currency_pair: CurencyPair, settings: Settings) -> Iterator["Third"]:
        sql = f"SELECT t,oanda,state FROM currency_third where state is null " \
              f"and currency_pair='{currency_pair.encode()}'"
        cls.cursor.execute(sql)
        for line in cls.cursor.fetchall():
            time = currency_pair.currency_main.period.utc(datetime.utcfromtimestamp(line[0]))
            third = cls(time=time, currency_pair=currency_pair, settings=settings)
            third.trade.oanda = line[1]
            third.trade.state = line[2]
            yield third

    def enter_close(self) -> float:
        return next(self.currency_pair.currency_main.left(time=self.time, n=1)).close

    def atr(self) -> float:
        return self.currency_pair.currency_main.atr(self.time)

    def is_close(self, time: datetime) -> bool:
        if self.currency_pair.currency_main.period.get_working_bars(start=self.time, end=time) > self.n:
            return True
        else:
            return False

    def result(self, time: datetime):
        time = self.currency_pair.currency_main.period.utc(time)
        if self.n is not None:
            if self.gain_mean > 0:
                for i in range(self.close.size):
                    if self.low[i] < - self.settings.stop:
                        self.trade.update(gain=-self.settings.stop, c=i, state="STOP")
                        break

                    if self.high[i] > self.settings.take:
                        self.trade.update(gain=self.settings.take, c=i, state="TAKE")
                        break

                    if self.low[i] < self.mean[i] - self.settings.stop:
                        self.trade.update(gain=self.close[i], c=i, state="LOW")

                        break
                    if self.high[i] > self.mean[i] + self.settings.take:
                        self.trade.update(gain=self.close[i], c=i, state="HIGH")
                        break

                if self.trade.state is None and self.is_close(time=time):
                    self.trade.update(gain=self.close[self.n], c=self.n, state="CLOSE")

            else:
                for i in range(self.close.size):
                    if self.high[i] > self.settings.stop:
                        self.trade.update(gain=-self.settings.stop, c=i, state="STOP")
                        break

                    if self.low[i] < - self.settings.take:
                        self.trade.update(gain=self.settings.take, c=i, state="TAKE")
                        break

                    if self.high[i] > self.mean[i] + self.settings.stop:
                        self.trade.update(gain=-self.close[i], c=i, state="LOW")
                        break

                    if self.low[i] < self.mean[i] - self.settings.take:
                        self.trade.update(gain=-self.close[i], c=i, state="HIGH")
                        break

                if self.trade.state is None and self.is_close(time=time):
                    self.trade.update(gain=-self.close[self.n], c=self.n, state="CLOSE")

    def save(self):
        if self.n is not None:
            sql = f"UPDATE currency_third set " \
                  f"gain={null(self.trade.gain)}," \
                  f"state={null(self.trade.state)}," \
                  f"c={null(self.trade.c)}," \
                  f"oanda={null(self.trade.oanda)} " \
                  f"where t={self.time.timestamp()} and currency_pair='{self.currency_pair.encode()}'"
            self.cursor.execute(sql)
            self.connection.commit()


def run_history(currency_pair: CurencyPair, time_interval: TimeInterval, third_config: Third.Config) -> Iterator[Third]:
    time = time_interval.start
    while time < time_interval.end:
        time += currency_pair.currency_main.period.delta
        if time.weekday() in [5, 6]:
            continue
        third = Third(time=time, currency_pair=currency_pair, settings=third_config.settings)
        if third.n is not None:
            yield third

# if __name__ == '__main__':
#     c = Third.Config.init_from_file()
#     currency_pair = c.currency_pairs[0]
#     from datetime import timedelta
#
#     t = datetime.now() - timedelta(days=500)
#
#     third = Third(time=t, currency_pair= currency_pair, settings=c.settings)
#
#     a = 1
