from currency.result_greed import run_history, Config
from datetime import datetime
import os
import csv

c = Config.init_from_file()

os.chdir("data")
name = f"g{c.enter}-{c.stop_coef}-{c.history_min}-{c.probability}-{datetime.now()}.csv"
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "State", "History", "Open", "Close", "s/b"])

for curr in c.curency:
    print(curr.name)
    for i in run_history(
            curr=curr, start=c.start, end=c.end, probability=0.85, number_bars=c.number_bars, history_min=c.history_min,
            enter=c.enter, stop_coef=c.stop_coef, skip_open=c.skip_open, skip_close=c.skip_close):
        writer.writerow([curr.name] + i)

f.close()
