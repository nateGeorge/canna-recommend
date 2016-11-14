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
from pymongo import MongoClient
import matplotlib.pyplot as plt

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

def get_mongo_data():
    '''
    retrieves saved data from mongo and returns as lists for further processing
    '''
    client = MongoClient()
    db = client['analytical360']
    coll = db['archives']
    all_entries = list(coll.find())
    cannabinoids, terpenes, clean_names, im_sources, isedible, links, names, save_path = [], [], [], [], [], [], [], []
    for a in all_entries:
        cannabinoids.append(a['cannabinoids'])
        terpenes.append(a['terpenes'])
        clean_names.append(a['clean_name'])
        im_sources.append(a['im_source'])
        isedible.append(a['isedible'])
        links.append(a['link'])
        names.append(a['name'])
        save_path.append(a['save_path'])

    return cannabinoids, terpenes, clean_names, im_sources, isedible, links, names, save_path

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

    # for scraping entire archives...gets links from all pages
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
    else:
        to_scrape_df = pd.read_pickle('analytical360/to_scrape_df.pk')

    scrape_archives = False
    if scrape_archives:
        # first, check which entries are already in the db, and don't use those
        client = MongoClient()
        db = client['analytical360']
        coll = db['archives']
        links = []
        for d in coll.find():
            links.append(d['link'])

        links = set(links)
        scrape_left = to_scrape_df[~to_scrape_df['link'].isin(links)]
        client.close()
        pool_size = mp.cpu_count()
        pool = mp.Pool(processes=pool_size)
        # breaks up DF into 16 parts
        chunks = 16
        df_step = int(round(scrape_left.shape[0] / float(chunks)))
        chunks_16 = [scrape_left.iloc[i*df_step:(i+1)*df_step] for i in range(chunks)]
        #test_chunks = [to_scrape_df.iloc[i*5:(i+1)*5] for i in range(chunks)]
        # all_stuff = []
        # for i in range(4):
        #     all_stuff.append(pool.map(func=scrape_cann_terps_from_arch, iterable=chunks_16[i*4:(i+1)*4]))
        # for mapping chunks
        stuff = pool.map(func=scrape_cann_terps_from_arch, iterable=chunks_16)
        #cannabinoids, terpenes, im_sources, no_imgs, names, clean_names, links = scrape_cann_terps_from_arch(scrape_left)

    make_dfs = True
    if make_dfs:
        # grabs data from mongo and converts to dataframe
        cannabinoids, terpenes, clean_names, im_sources, isedible, links, names, save_path = get_mongo_data()
        full_df = sc3.parse_raw_scrape(cannabinoids, terpenes, names)
        full_df['isedible'] = isedible
        full_df['filename'] = [f.split('/')[-1] for f in save_path]
        full_df['clean_name'] = clean_names
        skip_cols = set(['name', 'isedible', 'filename', 'clean_name'])
        for c in full_df.columns:
            print c
            if c in skip_cols:
                continue

            full_df[c] = pd.to_numeric(full_df[c])

        cannabinoids, terpenes, no_imgs, im_sources, names, clean_names = sc3.load_raw_scrape()
        full_df2 = sc3.parse_raw_scrape(cannabinoids, terpenes, names)
        full_df2['isedible'] = 0
        flow_df = pd.read_pickle('analytical360/flow_df.pk')
        clean_flow = sc3.clean_flow_df(flow_df, clean_names)
        # to match up names with clean_names...
        filenames = []
        rows_iter = clean_flow.iterrows()
        for c in clean_names:
            i, next_r = rows_iter.next()
            while next_r['clean_name'] != c:
                i, next_r = rows_iter.next()
            filenames.append(next_r['im_name'])

        full_df2['filename'] = filenames
        full_df2['clean_name'] = clean_names
        for c in full_df2.columns:
            print c
            if c in skip_cols:
                continue

            full_df2[c] = pd.to_numeric(full_df2[c])

        all_df = full_df.append(full_df2)
        # remove edibles, other junk...extracts, trim, etc
        all_df = all_df[all_df['isedible'] == 0]
        all_df = all_df[all_df['thc_total'] < 35.]
        all_df = all_df[all_df['thc_total'] > 1.]
        all_df = all_df[all_df['cbd_total'] < 25.] # no flowers over 25 so far...

        # need to get rid of concentrates...
        mask = []
        for i, r in all_df.iterrows():
            if r['clean_name'].find('hash') != -1 or r['clean_name'].find('kief') != -1 or r['clean_name'].find('trim') != -1:
                mask.append(0)
            else:
                mask.append(1)

        mask = np.array(mask) # could've been done in one step I think
        mask = np.array(mask == 1)

        all_df['mask'] = mask
        all_df = all_df[mask]
        plt.rcParams.update({'font.size': 18})
        all_df['thc_total'].hist(bins=50)
        plt.xlabel('total THC %')
        plt.ylabel('frequency')
        plt.show()
        all_df['cbd_total'].hist(bins=50)
        plt.xlabel('total CBD %')
        plt.ylabel('frequency')
        plt.show()
        # temp_df = all_df[all_df['cbd_total'] > 1.]
        # temp_df['cbd_total'].hist(bins=50)
        # plt.show()
        top_cbd = all_df.sort_values(by = 'cbd_total', ascending=False)
        top_lim = all_df.sort_values(by = 'Limonene', ascending=False)
        top_lin = all_df.sort_values(by = 'Linalool', ascending=False)
        more_skip_cols = set(['thc', 'cbd', 'activated_total']) # these don't seem to be important or make much sense
        # Ocimene has low variance as well
        # combine alpha and beta pinene to make one (beta has low abs values)
        # also ignore cbda, thca, since these will get activated.  can use thc_total etc
        all_skips = more_skip_cols | skip_cols
        # plots different columns
        # for c in all_df.columns:
        #     print c
        #     if c in skip_cols:
        #         continue
        #     all_df[c].hist(bins=50)
        #     plt.title(c)
        #     plt.show()

        drop_cols = ['thc', 'cbd', 'activated_total', 'Ocimene', 'beta_pinene', 'cbda', 'thca']

        for c in drop_cols:
            print c
            all_df.drop(c, axis=1, inplace=True)

        matches = sc3.match_up_leafly_names(all_df['clean_name'])
        # make lookup dict for translating ana360 names to leafly names
        match_dict = {}
        match_names = [] # list of clean_names from ana360 in leafly
        for m in matches:
            match_dict[m[1]] = m[0]
            match_names.append(m[1])

        match_names = set(match_names)

        mask = []
        leaf_df = all_df.copy()
        for i, r in leaf_df.iterrows():
            if r['clean_name'] in match_names:
                leaf_df.set_value(i, 'name', match_dict[r['clean_name']])
                mask.append(1)
            else:
                mask.append(0)

        mask = np.array(mask)
        mask = np.array(mask == 1)
        leaf_df = leaf_df[mask]

        all_df.to_pickle('analytical360/data_df_11-13-2016.pk')
        leaf_df.to_pickle('analytical360/leafly_matched_df_11-13-2016.pk')

        print leaf_df.groupby('name').count().shape[0], 'unique strains overlapping with leafly'

        # not sure if I want to do this...
        #all_df['pinene'] = all_df['alpha_pinene'] + all_df['alpha_pinene']



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
