import requests
import json
import os
from currency.utils import Currency, Daily
from currency.oanda import Config, h
from pprint import pprint


class Trade:
    def __init__(self, config: Config, currency: Currency, i: int, units: int = None, take: float = None,
                 stop: float = None):
        self.id = i
        self.config = config
        self.currency = currency
        self.headers = h(config.beaver)

    @classmethod
    def create(cls, config: Config, currency: Currency, units: int, take: float, stop: float):
        url = f"https://api-fxpractice.oanda.com/v3/accounts/{config.account}/orders"
        data = {
            "order": {
                "units": units,
                "instrument": currency.oanda,
                "type": "MARKET",
                "takeProfitOnFill": {
                    "price": str(take)
                },
                "stopLossOnFill": {
                    "price": str(stop)
                }
            }
        }
        req = requests.post(url, headers=h(config.beaver), data=json.dumps(data)).json()
        return cls(config=config, currency=currency, i=req["orderFillTransaction"]["id"], units=units, take=take,
                   stop=stop)

    def close(self):
        url = f"https://api-fxpractice.oanda.com/v3/accounts/{self.config.account}/trades/{self.id}/close"
        req = requests.put(url=url, headers=self.headers)
        return req.json()


if __name__ == '__main__':
    home = os.path.join(os.path.dirname(__file__), "..", "..")

    c = Config.init_from_file(path=home)
    # Trade.create(c, Currency("eur"), 100000, 1.25, 1.09)
    t = Trade(c, Currency(first="eur", period=Daily(1)), 183)
    pprint(t.close())
