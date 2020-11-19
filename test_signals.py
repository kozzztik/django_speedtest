import timeit
import django
from django import dispatch

RECEIVERS_COUNT = 100
REPEAT_COUNT = 1000000


class Receiver:
    value = 0

    def __call__(self, **kwargs):
        self.value += 1


signal = dispatch.Signal()

receivers = []

for i in range(100):
    r = Receiver()
    receivers.append(r)
    signal.connect(r)


def test():
    signal.send(Receiver)

print(django.VERSION)
print(timeit.timeit(test, number=REPEAT_COUNT))
