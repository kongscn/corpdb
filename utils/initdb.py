#! /usr/env python3
# -*- coding: utf-8 -*-

"""
Created on Jun 4, 2013

@author: kongs
"""

import csv
from os.path import abspath, dirname
from os.path import join as pjoin

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from corpdb.models import *

DATA_PATH = pjoin(abspath(dirname(dirname(__file__))),
                  'data')


@transaction.commit_on_success
def InitCountries():
    if Country.objects.count() > 0:
        return

    en_county_file = pjoin(DATA_PATH, 'country_en.csv')
    cn_county_file = pjoin(DATA_PATH, 'country_zh_hans.csv')

    countries_en = list(csv.DictReader(open(en_county_file, 'r', encoding='utf-8')))
    countries_cn = list(csv.DictReader(open(cn_county_file, 'r', encoding='utf-8')))
    countries_cn = {c['iso']: c['name'] for c in countries_cn}

    for item in countries_en:
        country = Country(
            iso=item['iso'],
            name=countries_cn.get(item['iso'], ''),
            name_en=item['name'],
        )
        country.save()

    print('Init countries: succeed')


@transaction.commit_on_success
def InitCnDistricts():
    if District.objects.count() > 0:
        return

    district_file = pjoin(DATA_PATH, 'cn_postcode_phonecode.csv')

    cn = Country.objects.get(iso='CN')

    recs = list(csv.DictReader(open(district_file, 'r', encoding='utf-8')))
    provinces = {}
    cities = {}

    for r in recs:
        zipcode = ''
        p = provinces.get(r['省'], None)
        if not p:
            # Insert province
            p = District(name=r['省'], level=1, country=cn)
            p.save()
            provinces[r['省']] = p

        if r['市']:
            if not r['区县']:
                zipcode = r['邮政编码']
            c = cities.get(r['省'] + r['市'], None)
            if not c:
            # Insert city
                c = District(name=r['市'], level=2, parent=p,
                             zipcode=zipcode, country=cn)
                c.save()

                cities[r['省'] + r['市']] = c

            if r['区县']:
                zipcode = r['邮政编码']
                z = District(name=r['区县'], level=3, parent=c,
                             zipcode=zipcode, country=cn)
                z.save()

    print('Init districts: succeed')


@transaction.commit_on_success
def InitExchanges():
    if Exchange.objects.count() > 0:
        return

    e = Exchange(symbol='SSE', name='上海证券交易所')
    e.save()
    sub_e = Exchange(symbol='A', name='A Share', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='B', name='B Share', parent=e)
    sub_e.save()

    e = Exchange(symbol='SZSE', name='深圳证券交易所')
    e.save()
    sub_e = Exchange(symbol='A', name='A Share', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='B', name='B Share', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='中小企业版', name='中小企业版', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='创业板', name='创业板', parent=e)
    sub_e.save()

    e = Exchange(symbol='NASDAQ', name='NASDAQ')
    e.save()
    sub_e = Exchange(symbol='CM', name='Capital Market', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='GM', name='Global Market', parent=e)
    sub_e.save()
    sub_e = Exchange(symbol='GS', name='Global Select', parent=e)
    sub_e.save()

    print('Init exchanges: succeed')


@transaction.commit_on_success
def InitSZStock():
    if Product.objects.count() > 0:
        return
    sz_file = pjoin(DATA_PATH, 'szse-all.csv')

    cn = Country.objects.get(iso='CN')
    sz_ex = Exchange.objects.get(symbol='SZSE', parent=None)
    recs = csv.DictReader(open(sz_file, 'r', encoding='utf-8'))

    for r in recs:
        c_symbol = r['公司代码'].zfill(6)
        c_name = r['公司简称'].replace(' ', '')
        c_name_full = r['公司全称'].strip()
        c_name_en = r['英文名称'].strip()
        c_prov = r['省 份'].strip()
        c_city = r['城 市'].strip()

        province = District.objects.get(name__startswith=c_prov, parent=None)

        try:
            city = District.objects.get(name=c_city, parent=province)
        except ObjectDoesNotExist:
            city = None
            print('City %s not found.' % c_city)

        comp = Company(symbol=c_symbol, name=c_name, name_full=c_name_full,
                       name_en=c_name_en, country=cn)

        comp.save()

        comp.districts.add(province)

        if city:
            comp.districts.add(city)

        for c in 'AB':
            if r[c + '股代码']:
                sub_ex = Exchange.objects.get(symbol=c, parent=sz_ex)

                product = Product(symbol=r[c + '股代码'].zfill(6),
                                  name=r[c + '股简称'].replace(' ', ''),
                                  company=comp,
                                  market_cap=int(r[c + '股流通股本'].strip()),
                                  ipo_date=r[c + '股上市日期'].strip(),
                                  yahoo_sfx='.SZ',
                                  )
                product.save()
                product.exchanges.add(sz_ex)
                product.exchanges.add(sub_ex)

    print('Initialize SZStocks: succeed')


@transaction.commit_on_success
def ImportNasdaqStock(file, ex, sub_ex):
    if sub_ex.product_set.count() > 0:
        return

    recs = csv.DictReader(open(file, 'r', encoding='utf-8'))

    for r in recs:
        c_name = r['Name'].strip()
        cq = Company.objects.filter(name=c_name)
        if len(cq) == 0:
            comp = Company(name=c_name, name_full=c_name, name_en=c_name)
            comp.save()
        elif len(cq) == 1:
            comp = cq[0]
        else:
            raise Exception

        product = Product(symbol=r['Symbol'].strip(), company=comp,
                          market_cap=int(float(r['MarketCap'].strip())),
                          ipo_date='' if r['IPOyear'] == 'n/a'
                          else r['IPOyear'].strip())

        product.save()
        product.exchanges.add(ex, sub_ex)


def InitNasdaqStock():
    nasdaq_ex = Exchange.objects.get(symbol='NASDAQ', parent=None)
    if nasdaq_ex.product_set.count() > 0:
        return

    cm_file = pjoin(DATA_PATH, 'nasdaq-cm.csv')
    gm_file = pjoin(DATA_PATH, 'nasdaq-gm.csv')
    gs_file = pjoin(DATA_PATH, 'nasdaq-gs.csv')

    ex_get = Exchange.objects.get
    sub_exes = {'CM': {'file': cm_file,
                       'sub_ex': ex_get(symbol='CM', parent=nasdaq_ex),
                       },
                'GM': {'file': gm_file,
                       'sub_ex': ex_get(symbol='GM', parent=nasdaq_ex),
                       },
                'GS': {'file': gs_file,
                       'sub_ex': ex_get(symbol='GS', parent=nasdaq_ex),
                       },
                }

    for key in sub_exes:
        ImportNasdaqStock(sub_exes[key]['file'],
                          nasdaq_ex, sub_exes[key]['sub_ex'])

    print('Initialize NasdaqStocks: succeed')


def init_db():
    InitCountries()

    InitCnDistricts()

    InitExchanges()

    InitSZStock()

    InitNasdaqStock()
