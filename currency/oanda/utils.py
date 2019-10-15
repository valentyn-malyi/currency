import json
import os

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))


class Units:
    def __init__(self, first: int, greed: int, third: int):
        self.first = first
        self.greed = greed
        self.third = third

    @classmethod
    def init_from_dict(cls, d: dict) -> "Units":
        first = d["first"]
        greed = d["greed"]
        third = d["third"]
        return cls(first=first, greed=greed, third=third)


class Config:
    config_name = "oanda.json"

    def __init__(self, beaver: str, account: str, units: Units):
        self.account = account
        self.beaver = beaver
        self.units = units

    @classmethod
    def init_from_file(cls) -> "Config":
        d = json.load(open(os.path.join(HOME, cls.config_name)))
        beaver = d["beaver"]
        account = d["account"]
        units = Units.init_from_dict(d["units"])

        return cls(beaver=beaver, account=account, units=units)


def h(beaver: str) -> dict:
    headers = {'Authorization': f'Bearer {beaver}',
               "Content-Type": "application/json"}
    return headers
