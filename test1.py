from currency.currency import Currency, Daily, H8, H4
from datetime import datetime
from currency.best_similar import main
from pytz import timezone
import os
import csv

start = datetime(year=2010, month=1, day=1, tzinfo=timezone('UTC'))
end = datetime(year=2018, month=12, day=1, tzinfo=timezone('UTC'))
probability = 0.85
main([Currency("eurusd",Daily(number_bars=2500))],probability=probability,start=start,end=end,number_bars=50)
