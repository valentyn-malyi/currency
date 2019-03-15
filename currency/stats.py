import numpy
import datetime


def create_stats_file(start: int, end: int, n, name: str):
    s = open(name)
    s.readline()
    f = open("stats_" + str(n) + "_" + name, "w")

    class Info:
        def __init__(self, gain, days, history, sd, mean):
            self.gain = gain
            self.days = days
            self.history = history
            self.sd = sd
            self.mean = mean

    indexes = {"history": [], "days": [], "sd": [], "mean": []}

    class Date:
        def __init__(self, y: int):
            self.y = y
            self.l = datetime.datetime(year=y, month=1, day=1).timestamp()
            self.r = datetime.datetime(year=y + 1, month=1, day=1).timestamp()

    dates = [Date(i) for i in range(start, end)]
    stats = {}

    for date in dates:
        stats[date.y] = []

    for line in s:
        line = line.split(";")
        indexes["history"].append(int(line[5]))
        indexes["days"].append(int(line[3]))
        indexes["sd"].append(float(line[6]))
        indexes["mean"].append((float(line[7])))
        for date in dates:
            if date.l <= int(datetime.datetime.strptime(line[1], "%Y-%m-%d %H:%M:%S").timestamp()) < date.r:
                stats[date.y].append(Info(float(line[2]), int(line[3]), int(line[5]), float(line[6]), float(line[7])))

    def quantile(target, round_n=2):
        target_set = set()
        for i in range(n):
            target_set.add(round(numpy.quantile(target, i / n), round_n))
        target = list(target_set)
        target.sort()
        return target + [float("inf")]

    indexes["history"] = quantile(target=indexes["history"], round_n=0)
    indexes["days"] = quantile(target=indexes["days"], round_n=0)
    indexes["sd"] = quantile(target=indexes["sd"], round_n=2)
    indexes["mean"] = quantile(target=indexes["mean"], round_n=2)

    def save_targets(stat, index, target):
        for history in range(len(target) - 1):
            slice_data = [i.gain for i in stat if target[history] <= i.__dict__[index] < target[history + 1]]
            if len(slice_data):
                f.write("{};".format(sum(slice_data)))
                # f.write("{};{};{};".format(sum(slice_data), sum(slice_data) / len(slice_data), len(slice_data)))
            else:
                # f.write("0;0;0;")
                f.write("0;")
        f.write("\n")

    for index in indexes:
        f.write("{};".format(index))
        for i in indexes[index]:
            # f.write("{};;;".format(i))
            f.write("{};".format(i))
        f.write("\n")
        for date in dates:
            f.write("{};".format(date.y))
            save_targets(stat=stats[date.y], index=index, target=indexes[index])
        f.write("\n\n")
