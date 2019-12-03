from datetime import datetime, timedelta
from currency.third.utils import Third
from currency.oanda.utils import Config as OandaConfig
from currency.oanda.trade import Trade

if __name__ == '__main__':
    third_config = Third.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()

    for currency_pair in third_config.currency_pairs:
        time = currency_pair.currency_main.period.utc(datetime.utcnow() + timedelta(hours=3))
        time = time.replace(day=20)
        if time.weekday() in [5, 6]:
            continue
        print(currency_pair, time)

        third = Third(time=time, currency_pair=currency_pair, settings=third_config.settings)
        print("CREATE", third)
        if third.n is not None:
            print("NEW:", third)
            third.save_first_time()

        for third in Third.get_from_table(currency_pair=currency_pair, settings=third_config.settings):
            print("GET", third)
            if third.trade.oanda is None:
                plus = abs(third.enter_close()) * third.atr()
                if third.direction == "buy":
                    take = third.enter_close() + plus * third.settings.take
                    stop = third.enter_close() - plus * third.settings.stop
                    trade = Trade.create(
                        config=oanda_config, currency=third.currency_pair.currency_main, units=oanda_config.units.third, take=take, stop=stop)
                else:
                    take = third.enter_close() - plus * third.settings.take
                    stop = third.enter_close() + plus * third.settings.stop
                    trade = Trade.create(
                        config=oanda_config, currency=third.currency_pair.currency_main, units=-oanda_config.units.third, take=take, stop=stop)
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
