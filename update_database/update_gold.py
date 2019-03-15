from datetime import datetime, timedelta
import os
import csv
import sqlite3
from pytz import timezone

conn = sqlite3.connect('../schemas/history/history.db')
cursor = conn.cursor()
os.chdir("../data/gold")

for csv_file in os.listdir("."):
    if csv_file.endswith(".csv"):
        print(csv_file)
        f = csv.DictReader(f=open(csv_file), delimiter=",")
        date_f = f.fieldnames[0]
        table_name = csv_file.split("_")
        table_name = "currency_" + table_name[0] + table_name[1]
        # noinspection SqlWithoutWhere
        cursor.execute("DELETE FROM {}".format(table_name))
        conn.commit()
        for line in f:
            time = datetime.strptime(line[date_f], "%b %d, %Y").replace(tzinfo=timezone('UTC'))
            if line.get("Time"):
                delta = datetime.strptime(line["<TIME>"], "%H:%M:%S")
                delta = timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
                time += delta
            time = time.timestamp()
            close = float(line["Price"].replace(",",""))
            high = float(line["High"].replace(",",""))
            low = float(line["Low"].replace(",",""))
            cursor.execute("INSERT into {} values (?,?,?,?)".format(table_name), [time, high, low, close])
        conn.commit()
