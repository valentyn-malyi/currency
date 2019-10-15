from datetime import datetime, timedelta
from currency.greed.utils import Greed
from currency.oanda.utils import Config as OandaConfig
from currency.oanda.trade import Trade
from currency.utils import TimeInterval

if __name__ == '__main__':
    greed_config = Greed.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()
    time_interval = TimeInterval.init_from_file()

    for curency in greed_config.curency:
        print(curency)
        time = curency.period.utc(datetime.utcnow() + timedelta(hours=3))
        print(time)
        if time.weekday() in [5, 6]:
            continue
        for greed in Greed.get_greed_from_table(curency, settings=greed_config.settings):
            print(greed)
            greed.get_gain()
            greed.update_right_bar(end=time)
            greed.check_open()

            if greed.trade.oanda is None and greed.trade.is_open() and greed.check_skip() and greed.trade.state is None:
                plus = abs(greed.day_enter_close()) * greed.atr()
                if greed.trade.direction == "sell":
                    take = greed.last_price() + plus * greed.settings.stop_coef
                    stop = greed.last_price() - plus
                    trade = Trade.create(config=oanda_config, currency=greed.currency, units=oanda_config.units.greed, take=take, stop=stop)
                else:
                    take = greed.last_price() - plus * greed.settings.stop_coef
                    stop = greed.last_price() + plus
                    trade = Trade.create(config=oanda_config, currency=greed.currency, units=-oanda_config.units.greed, take=take, stop=stop)
                print("OPEN:", trade)
                greed.trade.oanda = trade.id

            greed.check_end()

            if greed.trade.is_close():
                if greed.trade.oanda is not None:
                    trade = Trade(config=oanda_config, currency=greed.currency, i=greed.trade.oanda)
                    print("CLOSE:", greed)
            greed.save(end=time)

        greed = Greed(time=time, currency=curency, settings=greed_config.settings)
        if greed.len_greed >= greed_config.settings.history_min:
            greed.save_first_time()
            print("NEW:", greed)
