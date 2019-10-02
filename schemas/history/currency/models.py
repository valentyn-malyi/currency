from django.db import models


class Currency(models.Model):
    t = models.PositiveIntegerField(primary_key=True)
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()

    class Meta:
        abstract = True


class EurUsdDaily(Currency):
    pass


class GbpUsdDaily(Currency):
    pass


class UsdJpyDaily(Currency):
    pass


class UsdCadDaily(Currency):
    pass


class UsdChfDaily(Currency):
    pass


class AudUsdDaily(Currency):
    pass


class NzdUsdDaily(Currency):
    pass


class XauUsdDaily(Currency):
    pass


class Spx500UsdDaily(Currency):
    pass


class BcoUsdDaily(Currency):
    pass


class Greed(models.Model):
    t = models.PositiveIntegerField(null=False)
    currency = models.TextField(null=False)
    history = models.PositiveIntegerField(null=False)
    gain = models.FloatField(null=True)
    state = models.TextField(null=True)
    direction = models.TextField(null=True)
    o = models.PositiveIntegerField(null=True)
    c = models.PositiveIntegerField(null=True)
    oanda = models.PositiveIntegerField(null=True)
    str_datetime = models.TextField(null=False)
    last_update = models.PositiveIntegerField(null=False)
    str_last_update = models.TextField(null=False)

    class Meta:
        unique_together = (("t", "currency"),)


class First(models.Model):
    t = models.PositiveIntegerField(null=False)
    currency = models.TextField(null=False)
    history = models.PositiveIntegerField(null=False)
    gain_mean = models.FloatField(null=False)
    state = models.TextField(null=True)
    direction = models.TextField(null=False)
    n = models.PositiveIntegerField(null=False)
    oanda = models.PositiveIntegerField(null=True)
    str_datetime = models.TextField(null=False)
    c = models.PositiveIntegerField(null=True)
    gain = models.FloatField(null=True)

    class Meta:
        unique_together = (("t", "currency"),)


class Third(models.Model):
    t = models.PositiveIntegerField(null=False)
    currency_pair = models.TextField(null=False)
    gain_mean = models.FloatField(null=False)
    state = models.TextField(null=True)
    direction = models.TextField(null=False)
    n = models.PositiveIntegerField(null=False)
    oanda = models.PositiveIntegerField(null=True)
    str_datetime = models.TextField(null=False)
    c = models.PositiveIntegerField(null=True)
    gain = models.FloatField(null=True)

    class Meta:
        unique_together = (("t", "currency_pair"),)
