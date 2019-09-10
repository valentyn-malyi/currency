import json
import os

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))


class Log:
    def __init__(self, insert_bar):
        self.insert_bar = insert_bar

    @classmethod
    def init_from_dict(cls, d: dict) -> "Log":
        insert_bar = d.get("insert_bar")
        return cls(insert_bar=insert_bar)


class Config:
    config_name = "oanda.json"

    def __init__(self, beaver: str, account: str, log: Log, units: int):
        self.account = account
        self.beaver = beaver
        self.log = log
        self.units = units

    @classmethod
    def init_from_file(cls) -> "Config":
        d = json.load(open(os.path.join(HOME, cls.config_name)))
        beaver = d["beaver"]
        account = d["account"]
        units = d["units"]
        log = Log.init_from_dict(d["log"])

        return cls(beaver=beaver, account=account, log=log, units=units)


def h(beaver: str) -> dict:
    headers = {'Authorization': f'Bearer {beaver}',
               "Content-Type": "application/json"}
    return headers
