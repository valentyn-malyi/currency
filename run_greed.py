from currency.result_greed import main
from currency.currency import Currency, Daily, H8, H4
from datetime import datetime
from pytz import timezone
import os
import csv

# Ian put your parametrs
period = Daily(number_bars=2500)
curency = [
    Currency("gbpusd", period=period)
]

start = datetime(year=2010, month=1, day=1, tzinfo=timezone('UTC'))
end = datetime(year=2018, month=12, day=1, tzinfo=timezone('UTC'))
probability = 0.85
number_bars = 50
history_min = 20
enter = 0.2

# End Ian parametrs
os.chdir("data")
name = "g{}-{}-{}-{}-{}.csv".format(probability, number_bars, history_min, enter, datetime.now())
name = name.replace(" ", "-").replace(":", "-")
f = open("{}".format(name), "w")
writer = csv.writer(f, lineterminator="\n", delimiter=';')
writer.writerow(["Cur", "Date", "Gain", "State", "History", "Open", "Close", "s/b"])

for curr in curency:
    print(curr.name)
    for i in main(curr=curr, start=start, end=end, probability=0.85, number_bars=number_bars, history_min=history_min,
                  enter=enter):
        writer.writerow([curr.name] + i)

f.close()
