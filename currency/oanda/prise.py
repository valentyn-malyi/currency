import requests
import json
import os
import sqlite3
import datetime
from pprint import pprint


class Config:
    def __init__(self, beaver, account):
        self.account = account
        self.beaver = beaver

    @classmethod
    def init_from_file(cls, path) -> "Config":
        d = json.load(open(os.path.join(path, "oanda.json")))
        beaver = d["beaver"]
        account = d["account"]
        return cls(beaver=beaver, account=account)


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
    Currency("cad", reverse=True)
]

c = Config.init_from_file(path="../..")
conn = sqlite3.connect('../../schemas/history/history.db')
cursor = conn.cursor()

for cur in Currencies:
    url = f"https://api-fxpractice.oanda.com/v3/instruments/{cur.oanda}/candles?granularity=D&count=2&"

    headers = {'Authorization': f'Bearer {c.beaver}',
               "Content-Type": "application/json"}

    req = requests.get(url, headers=headers).json()
    pprint(req)

    for candle in req["candles"]:
        if candle["complete"]:
            print(candle["time"])
            # add six hours
            time = datetime.datetime.strptime(candle["time"], "%Y-%m-%dT%H:%M:%S.%f0000Z").timestamp() + 3600 * 6
            close = float(candle["mid"]["c"])
            high = float(candle["mid"]["h"])
            low = float(candle["mid"]["l"])
            print(time, high, low)
            cursor.execute(f"INSERT OR REPLACE into {cur.table} values ({time},{high},{low},{close})")
        conn.commit()
