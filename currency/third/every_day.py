from datetime import datetime, timedelta
from currency.third.utils import Third
from currency.oanda import Config as OandaConfig
from currency.oanda.trade import Trade
from currency.utils import TimeInterval

if __name__ == '__main__':
    third_config = Third.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()
    time_interval = TimeInterval.init_from_file()

    for currency_pair in third_config.currency_pairs:
        print(currency_pair)
        time = currency_pair.currency_main.period.utc(datetime.utcnow() + timedelta(hours=3))
        print(time)
        if time.weekday() in [5, 6]:
            continue

        third = Third(time=time, currency_pair=currency_pair, settings=third_config.settings)
        if third.n is not None:
            print("NEW:", third)
            third.save_first_time()

        for third in Third.get_from_table(currency_pair=currency_pair, settings=third_config.settings):
            if third.trade.oanda is None:
                plus = abs(third.enter_close()) * third.atr()
                if third.direction == "buy":
                    take = third.enter_close() + plus * third.settings.take
                    stop = third.enter_close() - plus * third.settings.stop
                    trade = Trade.create(
                        config=oanda_config, currency=third.currency_pair.currency_main, units=oanda_config.units, take=take, stop=stop)
                else:
                    take = third.enter_close() - plus * third.settings.take
                    stop = third.enter_close() + plus * third.settings.stop
                    trade = Trade.create(
                        config=oanda_config, currency=third.currency_pair.currency_main, units=-oanda_config.units, take=take, stop=stop)
                third.trade.oanda = trade.id
                print("OPEN:", trade)
                third.save()

            third.result(time=time)

            if third.trade.state is not None:
                if third.trade.oanda is not None:
                    trade = Trade(config=oanda_config, currency=third.currency_pair.currency_main, i=third.trade.oanda)
                    print(trade.close())
                print("CLOSE:", third)
                third.save()
