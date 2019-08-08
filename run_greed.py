from currency.result_greed import main
from currency.currency import Currency, Daily, H8, H4
from datetime import datetime
from pytz import timezone
from typing import List
import json
import os
import csv


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
    def init_from_file(cls):
        config = json.load(open(cls.config_name))
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
            curency.append(Currency(cur, period=period))
        return cls(
            curency=curency, start=start, end=end, probability=probability, number_bars=number_bars,
            history_min=history_min, enter=enter, stop_coef=stop_coef, skip_open=skip_open, skip_close=skip_close)


c = Config.init_from_file()

os.chdir("data")
name = f"g{c.enter}-{c.stop_coef}-{c.history_min}-{c.probability}-{datetime.now()}.csv"
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "State", "History", "Open", "Close", "s/b"])

for curr in c.curency:
    print(curr.name)
    for i in main(
            curr=curr, start=c.start, end=c.end, probability=0.85, number_bars=c.number_bars, history_min=c.history_min,
            enter=c.enter, stop_coef=c.stop_coef, skip_open=c.skip_open, skip_close=c.skip_close):
        writer.writerow([curr.name] + i)

f.close()
