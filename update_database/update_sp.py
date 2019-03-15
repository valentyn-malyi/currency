from datetime import datetime, timedelta
import os
import csv
import sqlite3
from pytz import timezone

conn = sqlite3.connect('../schemas/history/history.db')
cursor = conn.cursor()
os.chdir("../data/sp")

for csv_file in os.listdir("."):
    if csv_file.endswith(".csv"):
        print(csv_file)
        f = csv.DictReader(f=open(csv_file), delimiter=",")
        table_name = csv_file.split("_")
        table_name = "currency_" + table_name[0] + table_name[1]
        # noinspection SqlWithoutWhere
        cursor.execute("DELETE FROM {}".format(table_name))
        conn.commit()
        for line in f:
            print(line)
            time = datetime.strptime(line['Date'], "%Y-%m-%d").replace(tzinfo=timezone('UTC'))
            if line.get("Time"):
                delta = datetime.strptime(line["<TIME>"], "%H:%M:%S")
                delta = timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
                time += delta
            time = time.timestamp()
            close = float(line["Close"])
            high = float(line["High"])
            low = float(line["Low"])
            print(time,close)
            cursor.execute("INSERT into {} values (?,?,?,?)".format(table_name), [time, high, low, close])
        conn.commit()
