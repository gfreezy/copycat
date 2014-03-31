import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(BASE_DIR)
os.environ["DJANGO_SETTINGS_MODULE"] = "copycat.settings"


import requests
import urlparse
from bs4 import BeautifulSoup
from django_cron import CronJobBase, Schedule
from forum.models import CentralBank

HOST = 'http://cn.investing.com'
URL = 'http://cn.investing.com/central-banks'


def fetch_row_data(url=URL):
    req = requests.get(url)
    bs = BeautifulSoup(req.text)
    all_rows = bs.select('.crossRatesTbl tbody tr')
    for row in all_rows:
        yield parse_row(row)


def parse_row(row):
    name_col, bank_col, rate_col, next_metting_col, last_changed_col = row.find_all('td')
    classes = name_col.contents[0]['class']
    classes.remove('ceFlags')
    name = classes[0]
    url = bank_col.contents[0]['href']
    bank = ''.join(bank_col.stripped_strings).replace('&nbsp;', '').strip()
    rate = ''.join(rate_col.stripped_strings).replace('&nbsp;', '').strip()
    next_metting = ''.join(next_metting_col.stripped_strings).replace('&nbsp;', '').strip()
    last_changed = ''.join(last_changed_col.stripped_strings).replace('&nbsp;', '').strip()
    return name, bank, url, rate, next_metting, last_changed


def create(name, bank, url, rate, next_metting, last_changed):
    url = urlparse.urljoin(HOST, url)
    if CentralBank.objects.filter(name=name).exists():
        CentralBank.objects.filter(name=name).update(
            bank=bank, url=url, rate=rate, next_metting=next_metting, last_changed=last_changed
        )
    else:
        CentralBank.objects.create(
            name=name, bank=bank, url=url,
            rate=rate, next_metting=next_metting,
            last_changed=last_changed
        )


def process():
    for cols in fetch_row_data():
        create(*cols)


class CentralBankJob(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'forum.central_bank_job'    # a unique code

    def do(self):
        process()


if __name__ == '__main__':
    process()