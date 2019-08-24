import re
import itertools
from time import sleep
from urllib.parse import urljoin

import requests
from tabulate import tabulate
from lxml import html


HEADERS=['Date/Time', 'Level']
LOCATIONS = [
    'Half Moon Bay, California',
    'Huntington Beach',
    'Providence, Rhode Island',
    'Wrightsville Beach, North Carolina'
]


def main():
    for location in LOCATIONS:
        try:
            rows = tide_forecast(location)
            print("{:^45}".format(location), '\n')
            print(tabulate(rows, headers=HEADERS), '\n')
        except Exception as re:
            print(re)

        sleep(1) # be a good citizen


def tide_forecast(location):
    """
    Returns a list of tuples containing the time and level of low tides between
    sunrise and sunset for the given `location`
    """

    url = url_for_location(location)
    rows = scrape(url, xpath='//table[@class="tide-table"]/tr')
    header_indices = (i for i, row in enumerate(rows) if row[0].tag == 'th')
    partitions = partition(rows, lambda x: x[0].tag == 'th')

    results = list()
    for p in partitions:
        day = p[0][0].text_content().strip()
        target_rows = partition(p, lambda x: x[-1].text_content() in ('Sunrise', 'Sunset'))

        for row in target_rows:
            for cell in (r for r in row if r[-1].text_content() == 'Low Tide'):
                time, timezone, level, *_ = (c.text_content().strip() for c in cell)
                results.append((' '.join([day, time, timezone]), level))

    return results


def scrape(url, *, xpath):
    """
    returns lxml elements at `url` that match `xpath` expression
    """

    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        resp.raise_for_status()

    return html.fromstring(resp.content).xpath(xpath)

def url_for_location(location):
    """
    Convert a `location` into an endpoint where tide information can be scraped

    url paths for each location consist of alphanumerics separated by '-'
    where # is first converted to the word 'number'

    e.g. Elk River Railroad Bridge #18, Humboldt Bay, California becomes
         Elk-River-Railroad-Bridge-number-18-Humboldt-Bay-California
    """

    base_url = 'https://www.tide-forecast.com/locations/{}/tides/latest'
    path = re.sub(r'[^\w\s]', '', location.replace('#', 'number ')).replace(' ', '-')
    return base_url.format(path)


def partition(iterable, predicate):
    """
    partitions an iterable into a list of iterables based on a boundary predicate
    """

    a, b = itertools.tee(idx for idx, item in enumerate(iterable) if predicate(item))
    next(b, None)
    pairs = zip(a, b)
    return [iterable[i:j] for i, j in pairs]


if __name__ == '__main__':
    main()
