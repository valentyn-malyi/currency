from datetime import datetime, timedelta
from currency.first.utils import First
from currency.oanda.utils import Config as OandaConfig
from currency.oanda.trade import Trade
from currency.utils import TimeInterval

if __name__ == '__main__':
    first_config = First.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()
    time_interval = TimeInterval.init_from_file()

    for curency in first_config.curency:
        time = curency.period.utc(datetime.utcnow() + timedelta(hours=3))
        if time.weekday() in [5, 6]:
            continue
        print(curency, time)

        first = First(time=time, currency=curency, settings=first_config.settings)
        print("CREATE", first)

        if first.n is not None:
            print("NEW:", first)
            first.save_first_time()

        for first in First.get_from_table(currency=curency, settings=first_config.settings):
            print("GET", first)
            if first.trade.oanda is None:
                plus = abs(first.enter_close()) * first.atr()
                if first.direction == "buy":
                    take = first.enter_close() + plus * first.settings.take
                    stop = first.enter_close() - plus * first.settings.stop
                    trade = Trade.create(config=oanda_config, currency=first.currency, units=oanda_config.units.first, take=take, stop=stop)
                else:
                    take = first.enter_close() - plus * first.settings.take
                    stop = first.enter_close() + plus * first.settings.stop
                    trade = Trade.create(config=oanda_config, currency=first.currency, units=-oanda_config.units.first, take=take, stop=stop)
                first.trade.oanda = trade.id
                print("OPEN:", trade)
                first.save()

            first.result(time=time)

            if first.trade.state is not None:
                if first.trade.oanda is not None:
                    trade = Trade(config=oanda_config, currency=first.currency, i=first.trade.oanda)
                    print(trade.close())
                print("CLOSE:", first)
                first.save()
