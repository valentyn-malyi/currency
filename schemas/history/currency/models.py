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


class GoldDaily(Currency):
    pass


class EurUsdH8(Currency):
    pass


class GbpUsdH8(Currency):
    pass


class UsdJpyH8(Currency):
    pass


class UsdCadH8(Currency):
    pass


class UsdChfH8(Currency):
    pass


class AudUsdH8(Currency):
    pass


class NzdUsdH8(Currency):
    pass


class GoldH8(Currency):
    pass


class EurUsdH4(Currency):
    pass


class GbpUsdH4(Currency):
    pass


class UsdJpyH4(Currency):
    pass


class UsdCadH4(Currency):
    pass


class UsdChfH4(Currency):
    pass


class AudUsdH4(Currency):
    pass


class NzdUsdH4(Currency):
    pass


class GoldH4(Currency):
    pass


class SpDaily(Currency):
    pass


class OilDaily(Currency):
    pass
