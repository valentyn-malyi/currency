from datetime import datetime, timedelta
import os
import csv
import sqlite3
from pytz import timezone

conn = sqlite3.connect('../schemas/history/history.db')
cursor = conn.cursor()
os.chdir("../data/ian_data")

for csv_file in os.listdir("."):
    if csv_file.endswith(".csv"):
        print(csv_file)
        f = csv.DictReader(f=open(csv_file), delimiter=",")
        date_f = f.fieldnames[0]
        table_name = csv_file.split("_")
        table_name = "currency_" + table_name[0] + table_name[1]
        # noinspection SqlWithoutWhere
        for line in f:
            time = datetime.strptime(line["Time"], "%x").replace(tzinfo=timezone('UTC'))
            time = time.timestamp()
            close = float(line["Last"])
            high = float(line["High"])
            low = float(line["Low"])
            cursor.execute("INSERT OR REPLACE into {} values (?,?,?,?)".format(table_name), [time, high, low, close])
        conn.commit()
