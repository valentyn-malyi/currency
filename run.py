from currency.result import main
from currency.currency import Currency, Daily, H8, H4
from currency.stats import create_stats_file
from datetime import datetime
from pytz import timezone
import os
import csv

# Ian put your parametrs
period = H4(number_bars=7500)
curency = [
    Currency("eurusd", period=period)
]

start = datetime(year=2011, month=1, day=1, tzinfo=timezone('UTC'))
end = datetime(year=2011, month=2, day=1, tzinfo=timezone('UTC'))
probability = 0.99
number_bars = 50
history_min = 100
stop = 10
take = 10
start_n = 25
skip = 5/6

# End Ian parametrs
os.chdir("data")
name = "t{}-{}-{}-{}-{}-{}.csv".format(probability, number_bars, history_min, take, stop, datetime.now())
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "Days", "Exit", "History", "std", "mean"])

for curr in curency:
    print(curr.name)
    for i in main(curr=curr, start=start, end=end, probability=0.85, number_bars=number_bars, history_min=history_min,
                  stop=stop, take=take, skip=skip):
        writer.writerow([curr.name] + i)

f.close()
create_stats_file(start=start.year, end=end.year, n=start_n, name=name)
