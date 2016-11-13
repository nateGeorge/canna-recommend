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
import analytical360.scrape_360 as sc3
import multiprocessing as mp

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

def scrape_cann_terps_from_arch(df):
    cannabinoids, terpenes, im_sources, no_imgs, names, clean_names = sc3.scrape_site(df,
    base_im_path='analytical360/archive_images/',
    delay=0.25,
    mongo=['analytical360', 'archives'])
    links = df['link']
    return cannabinoids, terpenes, im_sources, no_imgs, names, clean_names, links

if __name__ == "__main__":
    # using requests: finding it hard to get all the correct entries
    MAIN_URL = 'http://analytical360.com/m/archived'
    res = requests.get(MAIN_URL)
    soup = bs(res.content, 'lxml')
    num_block = soup.findAll('div', {'class':'wpapi_pagination'})
    num_pages = int(num_block[0].findAll('span')[0].text.split()[-1])

    last_num_pages = 3823 # last time I checked
    if num_pages != last_num_pages:
        max_diff = num_pages - last_num_pages
        print max_diff, 'new pages'
        pages_left = range(1, max_diff+1)
        # scrape_newstuff(pages_left)

    #driver = setup_driver()
    # test scraping a few pages...
    # df, failed = scrape_newstuff(range(1, 11))

    # for scraping entire archives...
    scrape_all = False
    if scrape_all:
        df, failed = scrape_newstuff(range(1, num_pages + 1))
        df.to_pickle('analytical360/archives_links_df.pk')
    else:
        df = pd.read_pickle('analytical360/archives_links_df.pk')

    get_to_scrape = False
    if get_to_scrape:
        df['clean_name'] = df['name'].apply(sc3.clean_a_name)

        nameset = set(df['clean_name'].values)

        matches = sc3.match_up_leafly_names(nameset)

        matches_to_scrape = set([x[1] for x in matches])
        to_scrape_df = df[df['clean_name'].isin(matches_to_scrape)]
        to_scrape_df.to_pickle('analytical360/to_scrape_df.pk')


    to_scrape_df = pd.read_pickle('analytical360/to_scrape_df.pk')
    pool_size = mp.cpu_count()

    pool = mp.Pool(processes=pool_size)
    # breaks up DF into 16 parts
    chunks = 16
    df_step = int(round(to_scrape_df.shape[0] / float(chunks)))
    chunks_16 = [to_scrape_df.iloc[i*df_step:(i+1)*df_step] for i in range(chunks)]
    #test_chunks = [to_scrape_df.iloc[i*5:(i+1)*5] for i in range(chunks)]
    # all_stuff = []
    # for i in range(4):
    #     all_stuff.append(pool.map(func=scrape_cann_terps_from_arch, iterable=chunks_16[i*4:(i+1)*4]))
    stuff = pool.map(func=scrape_cann_terps_from_arch, iterable=chunks_16)
    #
    # cannabinoids = [x[0] for x in stuff]
    # terpenes = [x[1] for x in stuff]
    # im_sources = [x[2] for x in stuff]
    # no_imgs = [x[3] for x in stuff]
    # names = [x[4] for x in stuff]
    # clean_names = [x[5] for x in stuff]
    # links = [x[6] for x in stuff]

    # need to aggregate cannabinoids, etc for saving...

    #sc3.save_raw_scrape(cannabinoids, terpenes, im_sources, no_imgs, names, clean_names, prefix='archives/')
