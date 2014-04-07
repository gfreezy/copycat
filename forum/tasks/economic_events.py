import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(BASE_DIR)
os.environ["DJANGO_SETTINGS_MODULE"] = "copycat.settings"


import requests
import datetime
from hashlib import md5
from bs4 import BeautifulSoup
from django_cron import CronJobBase, Schedule
from forum.models import EconomicEvent
from django.utils import timezone


URL = 'http://cn.investing.com/economic-calendar/'


def fetch_row_data(url=URL):
    req = requests.get(url)
    req.encoding = 'utf8'
    bs = BeautifulSoup(req.text)
    all_rows = bs.find(id='ecEventsTable').find_all('tr')
    for row in all_rows:
        if not row.get('event_timestamp', ''):
            continue
        yield parse_row(row)


def parse_row(row):
    time = row['event_timestamp']
    classes = row.select('.flagCur')[0].contents[0]['class']
    classes.remove('ceFlags')
    country = classes[0]
    flag_cur = ''.join(row.select('.flagCur')[0].stripped_strings).replace('&nbsp;', '')
    txt_num = len(row.select('.textNum .grayFullBullishIcon'))
    event = ''.join(row.select('.event')[0].stripped_strings).replace('&nbsp;', '')
    act = ''.join(row.select('.act')[0].stripped_strings).replace('&nbsp;', '')
    fore = ''.join(row.select('.fore')[0].stripped_strings).replace('&nbsp;', '')
    prev = ''.join(row.select('.prev')[0].stripped_strings).replace('&nbsp;', '')

    return time, country, flag_cur, txt_num, event, act, fore, prev


def create_event(time, country, flag_cur, txt_num, event, act, fore, prev):
    s = '%s%s%s' % (time, flag_cur, event)
    ident = md5(s.encode('utf8')).hexdigest()
    if EconomicEvent.objects.filter(ident=ident).count():
        return

    t = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    t_ = timezone.make_aware(t, timezone.utc)
    ec = EconomicEvent.objects.create(
        time=t_, flag_cur=flag_cur, txt_num=txt_num,
        event=event, act=act, fore=fore, prev=prev,
        ident=ident, country=country,
    )
    return ec


def process():
    for cols in fetch_row_data():
        create_event(*cols)


class EconomicEventsJob(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'forum.ecnomic_events_job'    # a unique code

    def do(self):
        process()


if __name__ == '__main__':
    process()