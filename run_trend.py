from currency.currency import Currency, Daily, H8, H4
from datetime import datetime
from currency.best_similar import main
from pytz import timezone
import csv
import os

# Ian put your parametrs

period = H4(number_bars=7500)
start = datetime(year=2014, month=7, day=9, tzinfo=timezone('UTC'))
end = datetime(year=2014, month=7, day=10, tzinfo=timezone('UTC'))
probability = 0.85
number_bars = 50
take = 50
stop = 50
currs = [Currency("gbpusd", period=period), Currency("eurusd", period=period)]

# End Ian parametrs

os.chdir("data")
name = "b{}-{}-{}-{}-{}.csv".format(probability, number_bars, take, stop, datetime.now())
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "Days", "Exit", "History", "std", "mean"])
for i in main(currs=currs, probability=probability, start=start, end=end, number_bars=number_bars, take=take,
              stop=stop):
    writer.writerow(i)
