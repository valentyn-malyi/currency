import requests
import sqlite3
import datetime
import os
from currency.oanda import Config


class Currency:

    def __init__(self, name: str, reverse=False):
        if reverse:
            self.name = f"usd{name}"
            self.oanda = f"USD_{name.upper()}"
        else:
            self.name = f"{name}usd"
            self.oanda = f"{name.upper()}_USD"
        self.table = f"currency_{self.name}daily"


Currencies = [
    Currency("eur"),
    Currency("gbp"),
    Currency("jpy", reverse=True),
    Currency("aud"),
    Currency("nzd"),
    Currency("cad", reverse=True),
    Currency("chf", reverse=True)
]

if __name__ == '__main__':
    home = os.path.join(os.path.dirname(__file__), "..", "..")

    c = Config.init_from_file(path=home)
    conn = sqlite3.connect(os.path.join(home, "schemas", "history", "history.db"))
    cursor = conn.cursor()
    file_log = open(c.log.insert_bar, "a")

    for cur in Currencies:
        url = f"https://api-fxpractice.oanda.com/v3/instruments/{cur.oanda}/candles?granularity=D&count=3&"

        headers = {'Authorization': f'Bearer {c.beaver}',
                   "Content-Type": "application/json"}

        req = requests.get(url, headers=headers).json()

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
                file_log.write(f"{datetime.datetime.now()}|{cur.name}|{time.timestamp()}|{time}|{close}|{high}|{low}\n")

            file_log.flush()
            conn.commit()
