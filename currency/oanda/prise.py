from typing import List

import requests
import sqlite3
import datetime
import os
from currency.utils import Daily, Period, Currency
from currency.oanda import Config, h


def gen_currencies(period: Period) -> List[Currency]:
    currencies = [
        Currency(first="eur", period=period),
        Currency(first="gbp", period=period),
        Currency(second="jpy", period=period),
        Currency(first="aud", period=period),
        Currency(first="nzd", period=period),
        Currency(second="cad", period=period),
        Currency(second="chf", period=period),
        Currency(first="xau", period=period),
        Currency(first="spx500", period=period),
        Currency(first="bco", period=period)
    ]
    return currencies


if __name__ == '__main__':
    home = os.path.join(os.path.dirname(__file__), "..", "..")
    c = Config.init_from_file()
    conn = sqlite3.connect(os.path.join(home, "history.db"))
    cursor = conn.cursor()

    for cur in gen_currencies(period=Daily(1)):
        url = f"https://api-fxpractice.oanda.com/v3/instruments/{cur.oanda}/candles?granularity=D&count=3&"

        req = requests.get(url, headers=h(c.beaver)).json()

        for candle in req["candles"]:
            if candle["complete"]:
                # add six hours
                time = datetime.datetime.strptime(candle["time"] + "-0300", "%Y-%m-%dT%H:%M:%S.%f0000Z%z")
                if time.weekday() in {4, 5}:
                    continue
                close = float(candle["mid"]["c"])
                high = float(candle["mid"]["h"])
                low = float(candle["mid"]["l"])
                cursor.execute(f"INSERT OR REPLACE into {cur.table} values ({time.timestamp()},{high},{low},{close})")
                print(f"{datetime.datetime.now()}|{cur.name}|{time.timestamp()}|{time}|{close}|{high}|{low}\n")

            conn.commit()
