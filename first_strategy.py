from currency.utils import TimeInterval
from datetime import datetime
from currency.first.utils import First, run_history
import os
import csv

if __name__ == '__main__':

    first_config = First.Config.init_from_file()
    time_interval = TimeInterval.init_from_file()
    time_now = datetime.now()

    os.chdir("data")
    name = f"f1_{first_config.settings.probability}-{first_config.settings.number_bars}-{first_config.settings.history_min}-" \
           f"{first_config.settings.take}-{first_config.settings.stop}-{datetime.now()}.csv"
    name = name.replace(" ", "-").replace(":", "-")
    f = open("{}".format(name), "w")
    writer = csv.writer(f, lineterminator="\n", delimiter=';')
    writer.writerow(["Cur", "Date", "Gain", "Days", "Exit", "History", "mean", "State", "Close"])

    for curency in first_config.curency:
        print(curency.name)
        for first in run_history(curency=curency, time_interval=time_interval, first_config=first_config):
            first.result(time=time_now)
            print(first)
            writer.writerow([curency.name, first.time.date(), first.trade.gain, first.n, first.mean[first.n], first.history, first.sd[first.n],
                             first.trade.state, first.trade.c])
            f.flush()
