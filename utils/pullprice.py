import socket
import logging
import urllib.parse
import urllib.request
from urllib.error import URLError

# timeout in seconds
timeout = 6
socket.setdefaulttimeout(timeout)
logger = logging.getLogger(__name__)


def pull_price(symbol, startd=None, endd=None, period='d'):
    values = {}
    values['s'] = symbol
    if startd:
        values['a'] = startd.month - 1
        values['b'] = startd.day
        values['c'] = startd.year
    if endd:
        values['d'] = endd.month - 1
        values['e'] = endd.day
        values['f'] = endd.year
    values['g'] = period
    values['ignore'] = '.csv'

    url = r'http://ichart.finance.yahoo.com/table.csv'
    data = urllib.parse.urlencode(values)
    # usr_agent='Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)'
    # header={'User-Agent':usr_agent}
    # req = urllib.request.Request(url+'?'+data, headers=header)
    req = urllib.request.Request(url + '?' + data)
    # req = urllib.request.Request('http://ichart.finance.yahoo.com/table.csv?g=m&s=600000.SS')
    try:
        response = urllib.request.urlopen(req)
        content = response.read().decode()
        response.close()
        return content
    except (URLError, ConnectionResetError, socket.timeout) as e:
        logger.debug(str(e.__class__) + str(e))
        logger.debug(req.full_url)
        raise e