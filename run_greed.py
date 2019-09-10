from currency.utils import TimeInterval
from currency.greed.utils import Greed, run_history
from datetime import datetime
import os
import csv

greed_config = Greed.Config.init_from_file()
time_interval = TimeInterval.init_from_file()

os.chdir("data")
name = f"g{greed_config.settings.enter}-{greed_config.settings.stop_coef}-" \
       f"{greed_config.settings.history_min}-{greed_config.settings.probability}-{datetime.now()}.csv"
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "State", "History", "Open", "Close", "s/b"])

for curency in greed_config.curency:
    for greed in run_history(time_interval=time_interval, curency=curency, greed_config=greed_config):
        print(greed, curency.name)
        writer.writerow(
            [curency.name, greed.time.date(), greed.trade.gain, greed.trade.state, greed.len_greed, greed.trade.o, greed.trade.c,
             greed.trade.direction])
        f.flush()
