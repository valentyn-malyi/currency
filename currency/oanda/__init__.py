import json
import os


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


def h(beaver: str) -> dict:
    headers = {'Authorization': f'Bearer {beaver}',
               "Content-Type": "application/json"}
    return headers
