from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SectorStandard(models.Model):
    abbr = models.CharField(max_length=63, blank=True)
    name = models.CharField(max_length=63)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sector_standard'


@python_2_unicode_compatible
class Sector(models.Model):
    code = models.CharField(max_length=15, blank=True)
    name = models.CharField(max_length=63, )
    parent = models.ForeignKey('self', null=True, blank=True)
    standard = models.ForeignKey(SectorStandard,
                                 null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sector'


@python_2_unicode_compatible
class Country(models.Model):
    iso = models.CharField(max_length=2, blank=True)
    name = models.CharField(max_length=31, blank=True)
    name_en = models.CharField(max_length=63, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'country'


@python_2_unicode_compatible
class District(models.Model):
    name = models.CharField(max_length=15, blank=True)
    level = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True)
    zipcode = models.CharField(max_length=15, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'district'


@python_2_unicode_compatible
class Company(models.Model):
    symbol = models.CharField(max_length=15, blank=True)
    name = models.CharField(max_length=255, blank=True)
    name_full = models.CharField(max_length=255, blank=True)
    name_en = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    districts = models.ManyToManyField(District, null=True, blank=True)


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'company'


@python_2_unicode_compatible
class Exchange(models.Model):
    symbol = models.CharField(max_length=15, blank=True)
    name = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'exchange'


@python_2_unicode_compatible
class Product(models.Model):
    symbol = models.CharField(max_length=15)
    name = models.CharField(max_length=255, blank=True)
    exchange = models.ForeignKey(Exchange, null=True, blank=True)
    sub_exchange = models.ForeignKey(Exchange, null=True, blank=True, related_name='product_set_sub')
    sector = models.ForeignKey(Sector, null=True, blank=True)
    sub_sector = models.ForeignKey(Sector, null=True, blank=True, related_name='product_set_sub')
    company = models.ForeignKey(Company)
    market_cap = models.BigIntegerField(null=True, blank=True)
    ipo_date = models.CharField(max_length=10, blank=True)
    yahoo_sfx = models.CharField(max_length=5, blank=True)
    note = models.TextField(blank=True)

    exchange.short_description = 'Exchange'
    sub_exchange.short_description = 'Sub Exchange'

    sector.short_description = 'Sector'
    sub_sector.short_description = 'Sub Sector'

    def __str__(self):
        return self.symbol

    class Meta:
        db_table = 'product'

@python_2_unicode_compatible
class OHLC(models.Model):
    product = models.ForeignKey(Product)
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    adj_close = models.FloatField()
    volume = models.BigIntegerField()

    def __str__(self):
        return self.product

    class Meta:
        abstract = True
        index_together = [
            ['product', 'date'],
        ]

class OhlcD(OHLC):
    class Meta(OHLC.Meta):
        db_table = 'ohlc_d'


class OhlcW(OHLC):
    class Meta(OHLC.Meta):
        db_table = 'ohlc_w'


class OhlcM(OHLC):
    class Meta(OHLC.Meta):
        db_table = 'ohlc_m'


