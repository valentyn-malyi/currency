from currency.utils import TimeInterval
from datetime import datetime
from currency.third.utils import Third, run_history
import os
import csv

if __name__ == '__main__':

    third_config = Third.Config.init_from_file()
    time_interval = TimeInterval.init_from_file()

    os.chdir("data")
    name = f"f3_{third_config.settings.probability}-{third_config.settings.number_bars}-" \
           f"{third_config.settings.take}-{third_config.settings.stop}-{datetime.now()}.csv"
    name = name.replace(" ", "-").replace(":", "-")
    f = open("{}".format(name), "w")
    writer = csv.writer(f, lineterminator="\n", delimiter=';')
    writer.writerow(["Cur", "Date", "Gain", "Days", "Exit", "coef", "histry_day", "State"])

    for currency_pair in third_config.currency_pairs:
        print(currency_pair.encode())
        time_now = datetime.now()
        for third in run_history(currency_pair=currency_pair, time_interval=time_interval, third_config=third_config):
            third.result(time=time_now)
            writer.writerow(
                [currency_pair.encode(), third.time.date(), third.trade.gain, third.n, third.mean[third.n], third.coef, third.situation_time.date(),
                 third.trade.state])
            f.flush()
