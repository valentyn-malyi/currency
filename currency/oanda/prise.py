import requests
import json
import os
import sqlite3
import datetime


class Log:
    def __init__(self, insert_bar):
        self.insert_bar = insert_bar

    @classmethod
    def init_from_dict(cls, d: dict) -> "Log":
        insert_bar = d.get("insert_bar")
        return cls(insert_bar=insert_bar)


class Config:

    def __init__(self, beaver: str, account: str, log: Log):
        self.account = account
        self.beaver = beaver
        self.log = log

    @classmethod
    def init_from_file(cls, path) -> "Config":
        d = json.load(open(os.path.join(path, "oanda.json")))
        beaver = d["beaver"]
        account = d["account"]
        log = Log.init_from_dict(d["log"])

        return cls(beaver=beaver, account=account, log=log)


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

    c = Config.init_from_file(path="../..")
    conn = sqlite3.connect('../../schemas/history/history.db')
    cursor = conn.cursor()
    file_log = open(c.log.insert_bar, "a")

    for cur in Currencies:
        url = f"https://api-fxpractice.oanda.com/v3/instruments/{cur.oanda}/candles?granularity=D&count=2&"

        headers = {'Authorization': f'Bearer {c.beaver}',
                   "Content-Type": "application/json"}

        req = requests.get(url, headers=headers).json()

        for candle in req["candles"]:
            if candle["complete"]:
                # add six hours
                time = datetime.datetime.strptime(candle["time"], "%Y-%m-%dT%H:%M:%S.%f0000Z").timestamp() + 3600 * 6
                close = float(candle["mid"]["c"])
                high = float(candle["mid"]["h"])
                low = float(candle["mid"]["l"])
                cursor.execute(f"INSERT OR REPLACE into {cur.table} values ({time},{high},{low},{close})")
                file_log.write(f"{datetime.datetime.now()}|{cur.name}|{time}|{close}|{high}|{low}\n")
            conn.commit()
            file_log.flush()
