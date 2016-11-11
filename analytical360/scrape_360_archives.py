import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pandas as pd
import numpy as np
import re
import os
import cPickle as pk
import pandas as pd

ua = UserAgent()

def setup_driver():
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (ua.random)
    driver = webdriver.PhantomJS(desired_capabilities=dcap)
    driver.set_window_size(1920, 1080)
    return driver

def get_headers_cookies(driver):
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }
    cookies = driver.get_cookies()
    cooks = {}
    for c in cookies:
        cooks[c['name']] = c['value']  # map it to be usable for requests

    return headers, cooks

# using requests: finding it hard to get all the correct entries
MAIN_URL = 'http://analytical360.com/m/archived'
res = requests.get(MAIN_URL)
soup = bs(res.content, 'lxml')
num_block = soup.findAll('div', {'class':'wpapi_pagination'})
num_pages = int(num_block[0].findAll('span')[0].text.split()[-1])

last_num_pages == 3823 # last time I checked
if num_pages != last_num_pages:
    max_diff = num_pages - last_num_pages
    pages_left = range(1, max_diff+1)
    scrape_newstuff(pages_left)

driver = setup_driver()

def scrape_newstuff(pages_left):
    '''
    goes through each archive page, saves it, and grabs relevant links and names from it

    args: pages_left: list of pages to scrape
    '''
    links = []
    names = []
    failed = []
    arch_path = 'analytical360/archives_pages/'
    if not os.path.exists(arch_path):
        os.mkdir(arch_path)

    for i in pages_left:
        print i
        res = requests.get(MAIN_URL + '/page/' + str(i))
        if not res.ok:
            'print failed on:', MAIN_URL + '/page/' + str(i)
            time.sleep(1)
            res = requests.get(MAIN_URL + '/page/' + str(i))

        if not res.ok:
            failed.append(MAIN_URL + '/page/' + str(i))
            print 'failed twice'
            continue

        soup = bs(res.content)
        with open(arch_path + 'page' + str(i) + '.html', 'w') as f:
            f.write(res.content)

        #soup.find('ul', id='listlatestnews')
        boxes = soup.findAll('div', {'class':'postbox'})
        for b in boxes:
            a = b.find('a')
            if a:
                links.append(a.get('href'))
                names.append(a.text)
                print 'success!'
            else:
                print 'no link'
                failed.append(MAIN_URL + '/page/' + str(i))

    df = pd.DataFrame({'link':links, 'name':names})
    return df, failed

df, failed = scrape_newstuff(range(1, num_pages + 1))
