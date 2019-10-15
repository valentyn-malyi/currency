import json
import os

HOME = os.path.join(os.path.join(os.path.dirname(__file__), "..", ".."))

class Config:
    config_name = "oanda.json"

    def __init__(self, beaver: str, account: str, units: int):
        self.account = account
        self.beaver = beaver
        self.units = units

    @classmethod
    def init_from_file(cls) -> "Config":
        d = json.load(open(os.path.join(HOME, cls.config_name)))
        beaver = d["beaver"]
        account = d["account"]
        units = d["units"]

        return cls(beaver=beaver, account=account, units=units)


def h(beaver: str) -> dict:
    headers = {'Authorization': f'Bearer {beaver}',
               "Content-Type": "application/json"}
    return headers
