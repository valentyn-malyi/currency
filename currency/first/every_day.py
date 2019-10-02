from datetime import datetime
from currency.first.utils import First
from currency.oanda import Config as OandaConfig
from currency.oanda.trade import Trade
from currency.utils import TimeInterval

if __name__ == '__main__':
    first_config = First.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()
    time_interval = TimeInterval.init_from_file()

    for curency in first_config.curency:
        print(curency.name)
        time = curency.period.utc(datetime.now())
        if time.weekday() in [5, 6]:
            continue
        print(time)

        first = First(time=time, currency=curency, settings=first_config.settings)

        if first.n is not None:
            first.save_first_time()

        for first in First.get_from_table(currency=curency, settings=first_config.settings):

            if first.trade.oanda is None:
                print(first)
                plus = abs(first.enter_close()) * first.atr()
                if first.direction == "buy":
                    take = first.enter_close() + plus * first.settings.take
                    stop = first.enter_close() - plus * first.settings.stop
                    trade = Trade.create(config=oanda_config, currency=first.currency, units=oanda_config.units, take=take, stop=stop)
                else:
                    take = first.enter_close() - plus * first.settings.take
                    stop = first.enter_close() + plus * first.settings.stop
                    trade = Trade.create(config=oanda_config, currency=first.currency, units=-oanda_config.units, take=take, stop=stop)
                first.trade.oanda = trade.id
                print(trade.id)
                first.save()

            if first.is_close(time=time) and first.trade.oanda is not None:
                trade = Trade(config=oanda_config, currency=first.currency, i=first.trade.oanda)
                print(trade.close())
                first.result()
                print(first.trade.oanda)
                first.save()