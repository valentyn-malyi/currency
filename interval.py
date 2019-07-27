import numpy
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-p', '--percents', action='append', type=float, default=[], help='Add percent', )
parser.add_argument('name', help="File name")
parser.add_argument('number', type=int, help="Number of deals")
parser.add_argument('chooses', type=int, help="Number of chooses")
results = parser.parse_args()
name = results.name
n = results.number
ch = results.chooses
perc = results.percents

a = []
with open(name, "r") as f:
    for i in f:
        a.append(float(i))

v = []
x = range(n)

for i in range(ch):
    b = numpy.random.choice(a, n)
    c = numpy.cumsum(b)
    v.append(c)
    if i <= 500:
        plt.plot(x, c, "black")

v = numpy.array(v)

plt.grid(True)
plt.show()

for per in perc:
    plist = []
    for j in range(n):
        plist.append(numpy.percentile(v[:, j], per))
    plt.plot(x, plist)

plt.grid(True)
plt.show()
