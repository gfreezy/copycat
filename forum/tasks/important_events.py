import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(BASE_DIR)
os.environ["DJANGO_SETTINGS_MODULE"] = "copycat.settings"


import requests
import datetime
import pytz
from hashlib import md5
from bs4 import BeautifulSoup
from django_cron import CronJobBase, Schedule
from forum.models import ImportEvent
from django.utils import timezone


URL = 'http://www.dailyfx.com.hk/calendar/index.html'


def fetch_row_data(url=URL):
    req = requests.get(url)
    req.encoding = 'utf8'
    bs = BeautifulSoup(req.text, 'html.parser')
    all_rows = bs.select('#calTable .listtable tr[align]')
    for row in all_rows:
        yield parse_row(row)


def parse_row(row):
    tds = row.find_all('td')
    date = ''.join(tds[0].stripped_strings).strip()
    time = ''.join(tds[1].stripped_strings).strip()
    currency = ''.join(tds[2].stripped_strings).strip()
    event = ''.join(tds[3].stripped_strings).strip()
    t = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M')
    return t, currency, event


def create_event(t, currency, event):
    ident = md5((currency+event).encode('utf8')).hexdigest()
    if ImportEvent.objects.filter(ident=ident).exists():
        print 'exist'
        return

    t = timezone.make_aware(t, pytz.timezone('Asia/Shanghai'))
    ec = ImportEvent.objects.create(
        time=t,
        currency=currency,
        event=event,
        ident=ident,
    )
    return ec


def process():
    fetch_row_data()
    for cols in fetch_row_data():
        create_event(*cols)


class EconomicEventsJob(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'forum.important_events'    # a unique code

    def do(self):
        process()


if __name__ == '__main__':
    process()