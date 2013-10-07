import logging
import csv
import time as tm
from datetime import *
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.db.models import Q
from django.db import transaction

from corpdb.models import Product
from corpdb.models import OhlcD, OhlcW, OhlcM
from corpdb.utils.pullprice import pull_price


logger = logging.getLogger(__name__)

OHLCKlass = {'d': OhlcD,
             'w': OhlcW,
             'm': OhlcM,
             }


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-p', '--period',
                    action='store',
                    dest='period',
                    default='mwd',
                    help=('You can choose d for daily, w for weekly and '
                          'm for monthly data, or any combination, like dwm.'
                          'Default is mwd')
                    ),
        make_option('--retry',
                    type='int',
                    action='store',
                    dest='retry',
                    default=6,
                    help='Retry times. Default is 6.'),
    )

    def handle(self, *args, **options):
        logging.getLogger('corpdb.config').debug(options)
        update(period=options['period'], retry=options['retry'])


def update(period='dwm', retry=6, retry_wait=60 * 2):
    td = date.today()

    for p in period:
        # get last trading day

        if p == 'd':
            # yahoo historical prices are usually delayed
            td = td - timedelta(4)
            # last weekday
            # today=Sat.: -1 to get Friday,
            # today=Sun.: -2 to get Friday,
            last_trade = td - timedelta({6: 1, 7: 2}.get(
                td.isoweekday(), 0))

        elif p == 'w':
            # Monday of last full week
            # Get last Monday
            last_trade = td - timedelta(td.weekday())
            # Find last last Monday for possible delays
            last_trade = last_trade - timedelta(7)

        elif p == 'm':
            # Get first day of last month
            last_trade = (td.replace(day=1) - timedelta(1)).replace(day=1)

        else:
            raise Exception

        stocks = Product.objects.annotate(last_update=Max('ohlc' + p + '__date'))
        stocks = stocks.filter(
            Q(last_update=None) | Q(last_update__lt=last_trade)
        )

        update_list(stocks=stocks, period=p,
                    retry=retry, loop_after=retry_wait)


def update_list(stocks, period, retry=3, loop_after=60 * 2):
    """
    update ohlc_%period automatically
    """
    retry -= 1
    pre_str = '(%d atts) ' % retry
    len_stock = len(stocks)

    if len_stock == 0:
        logger.info('Finished update with no fails!')
        return True
    if retry < 0:
        logger.warning('Finished %s data update with %d fails' % (
            period, len_stock))
        for p in stocks:
            logger.error('Failed to insert symbols: %s %s',period, ' '.join([p.symbol for p in stocks]) )
            # logger.error(' '.join(['Fail:', period, p.symbol]))
        return False

    fails = []
    cur = 0

    for p in stocks:
        cur += 1
        if not p.last_update:
            p.last_update = date(1991, 1, 1)

        state = update_single(p, period=period)

        if state == 'DownloadFail':
            fails.append(p)
            logger.warning(pre_str + '%-6s %s download from %s failed.(%d/%d)' % (
                p.symbol, period, p.last_update, cur, len_stock))
        elif state == 'InsertError':
            fails.append(p)
            logger.error("%-6s %s insert failed!" % (p.symbol, period))
        else:
            logger.info(pre_str + '%-6s %4s %s records from %s inserted.(%d/%d)'
                        % (p.symbol, state, period,
                           p.last_update, cur, len_stock))
            if state > 1000:
                continue
        tm.sleep(2)
    if retry > 0:
        logger.info(pre_str +
                    'Current loop end. %d %s fails. Retry %d sec later.' %
                    (len(fails), period, loop_after))
        tm.sleep(loop_after)

    update_list(stocks=fails,
                period=period,
                retry=retry,
                loop_after=loop_after,
                )


@transaction.commit_on_success
def update_single(product, period):
    r = pull_price(symbol=product.symbol + product.yahoo_sfx,
                   startd=product.last_update,
                   period=period)
    if not r:
        return 'DownloadFail'
    r = r.strip().splitlines()
    r = r[2:-1]  # remove header, latest and last data(data on date_from).
    r.reverse()  # put older data ahead
    reader = csv.DictReader(r, fieldnames=[
        'Date', 'Open', 'High', 'Low',
        'Close', 'Volume', 'Adj Close'])

    for rec in reader:
        OHLCKlass[period](
            product=product,
            date=rec['Date'],
            open=rec['Open'],
            high=rec['High'],
            low=rec['Low'],
            close=rec['Close'],
            volume=rec['Volume'],
            adj_close=rec['Adj Close']
        ).save()

    return reader.line_num
