from datetime import datetime
from currency.greed.utils import Greed
from currency.oanda import Config as OandaConfig
from currency.oanda.trade import Trade
from currency.utils import TimeInterval

if __name__ == '__main__':
    greed_config = Greed.Config.init_from_file()
    oanda_config = OandaConfig.init_from_file()
    time_interval = TimeInterval.init_from_file()

    for curency in greed_config.curency:
        print(curency.name)
        time = curency.period.utc(datetime.now())
        if time.weekday() in [5, 6]:
            continue
        print(time)
        for greed in Greed.get_greed_from_table(curency, settings=greed_config.settings):
            print(greed)
            greed.get_gain()
            greed.trade.right_bar += 1
            greed.check_open()

            if greed.trade.oanda is None and greed.trade.is_open() and greed.check_skip() and greed.trade.state is None:
                plus = abs(greed.day_enter_close()) * greed.atr()
                if greed.trade.direction == "sell":
                    take = greed.last_price() + plus * greed.settings.stop_coef
                    stop = greed.last_price() - plus
                    trade = Trade.create(config=oanda_config, currency=greed.currency, units=oanda_config.units, take=take, stop=stop)
                else:
                    take = greed.last_price() - plus * greed.settings.stop_coef
                    stop = greed.last_price() + plus
                    trade = Trade.create(config=oanda_config, currency=greed.currency, units=-oanda_config.units, take=take, stop=stop)
                greed.trade.oanda = trade.id

            greed.check_end()

            if greed.trade.is_close():
                trade = Trade(config=oanda_config, currency=greed.currency, i=greed.trade.oanda)
                print(trade.close())
            greed.save()
        print("new")
        greed = Greed(time=time, currency=curency, settings=greed_config.settings)
        print(greed)
        if greed.len_greed >= greed_config.settings.history_min:
            greed.save_first_time()
