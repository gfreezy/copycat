#coding: utf8
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(BASE_DIR)
os.environ["DJANGO_SETTINGS_MODULE"] = "copycat.settings"


import requests
import datetime
import pytz
from hashlib import md5
import urlparse
from bs4 import BeautifulSoup
from django_cron import CronJobBase, Schedule
from forum.models import Forex

HOST = 'http://cn.reuters.com'
URLS = [
    'http://cn.reuters.com/investing/news/archive/vbc_cn_forex',
    'http://cn.reuters.com/investing/news/archive/vbc_eur_forex',
]


def fetch_row_data(url):
    req = requests.get(url)
    req.encoding = 'utf8'
    bs = BeautifulSoup(req.text)
    all_rows = bs.select('.primaryContent .headlineMed')
    for row in all_rows:
        yield parse_row(row)


def parse_row(row):
    link = row.find('a')
    title = link.string
    url = link['href']
    url = urlparse.urljoin(HOST, url)
    time = row.select('.timestamp')[0].string
    article = fetch_full_article(url)
    return time, title, url, article


def parse_time(t):
    seps = unicode(t).rsplit(u' ', 3)
    time = datetime.datetime.strptime(seps[-2], '%H:%M')
    if len(seps) > 2:
        date_str = seps[0].replace(' ', '')
        date = datetime.datetime.strptime(date_str.encode('utf8'), '%Y年%m月%d日')
    else:
        date = datetime.datetime.today()

    return datetime.datetime(date.year, date.month, date.day,
                             time.hour, time.minute, tzinfo=pytz.timezone('Asia/Shanghai'))


def fetch_full_article(url):
    url += '?sp=true'
    req = requests.get(url)
    req.encoding = 'utf8'
    bs = BeautifulSoup(req.text)
    paras = bs.select('#resizeableText .focusParagraph')
    paras_str = filter(None, [''.join(p.stripped_strings).strip() for p in paras])
    article = '\n'.join(paras_str)
    index = article.find(u'（完）')
    if index == -1:
        return article
    return article[:index]


def create(time, title, url, article):
    ident = md5((title+url).encode('utf8')).hexdigest()
    if Forex.objects.filter(ident=ident).exists():
        return
    t_ = parse_time(time)
    ec = Forex.objects.create(
        time=t_, title=title, url=url, ident=ident, article=article,
    )
    return ec


def process():
    for url in URLS:
        for cols in fetch_row_data(url):
            create(*cols)


class EconomicEventsJob(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'forum.forex_job'    # a unique code

    def do(self):
        process()


if __name__ == '__main__':
    process()