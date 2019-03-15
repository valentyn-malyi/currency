from currency.result import main
from currency.currency import Currency, Daily
from currency.stats import create_stats_file
from datetime import datetime
from pytz import timezone
import os
import csv

# Ian put your parametrs
period = Daily(number_bars=2500)
curency = [
    Currency("eurusd", period=period),
    Currency("gbpusd", period=period),
    Currency("usdjpy", period=period),
    Currency("audusd", period=period),
    Currency("nzdusd", period=period),
    Currency("usdcad", period=period),
    Currency("usdchf", period=period)
]

start = datetime(year=2010, month=1, day=1, tzinfo=timezone('UTC'))
end = datetime(year=2018, month=12, day=1, tzinfo=timezone('UTC'))
probability = 0.85
number_bars = 50
history_min = 20
stop = 9
take = 3
start_n = 25

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
                  stop=stop, take=take):
        writer.writerow([curr.name] + i)

f.close()
create_stats_file(start=start.year, end=end.year, n=start_n, name=name)
