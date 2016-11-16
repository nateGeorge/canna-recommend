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
from collections import deque
import string
import time
import psycopg2 as pg
from pymongo import MongoClient
import leafly.data_preprocess as dp
import leafly.scrape_leafly as sl

ua = UserAgent()
MAIN_URL = 'http://analytical360.com/testresults'

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

def check_rows(res):
    '''
    args: takes a requests object

    returns: all table rows in doc

    checks to make sure the request was successful and the data we want is
    there in the format we expect.  Otherwise throws an error
    '''
    soup = bs(res.content, 'lxml')
    rows = soup.findAll('tr', {'title': 'Click To View Detail Test Results'})
    if len(rows) == 0 or not res.ok:
        raise Exception('response returned:', res)
    return rows

def get_links(rows):
    '''
    take requests response object
    first checks to make sure there are any links in the row, if not, spits an
    error
    returns a list of unique links from all the rows
    '''
    links = set()
    for i, r in enumerate(rows):
        row_links = r.findAll('a')
        if len(row_links) == 0:
            raise Exception('no links in row', i)
        links = set(row_links) | links

    links = list(set([l.get('href') for l in links]))
    return links

def get_flower_links(rows):
    links = get_links(rows)
    flower_links = [l for l in links if re.search('.*flowers.*', l)]
    flower_rows = [r for r in rows if re.search('.*flowers.*', r.findAll('a')[0].get('href'))]
    return flower_links, flower_rows

def check_groups(links):
    '''
    args: takes in list of links from analytical360
    returns: unique product groups in links (i.e. edibles, flowers, etc)

    checks to make sure number of groups in still 6
    {'concentrates', 'edibles', 'flowers', 'liquids', 'listing', 'topicals'}
    '''
    groups = [l.split('/')[-2] for l in links]
    groups = list(set(groups))
    if len(groups) != 6:
        raise Exception('number of product groups has changed!')

    return groups

def make_links_dataframe(links):
    '''
    args: list of links

    returns: dataframe of links with product group, link
    '''
    df = pd.DataFrame({'link': links, 'product': [
                      l.split('/')[-2] for l in links]})
    return df

def extract_info(link):
    '''
    args: link to product page

    returns: dict or df of properties of product
    '''
    res = requests.get(link)
    s = bs(res.content)
    h3s = s.findAll('h3')
    if len(h3s) < 2:
        raise Exception('can\'t find title in:', link)
    name = h3s[1]

def get_links_selenium(driver):
    # right now only gets one link
    return driver.find_element_by_xpath('//*[@id="flowers"]/tbody/tr[1049]/td[1]/a')

def download_image(src, filename, headers, cooks):
    r = requests.get(src, headers=headers, cookies=cooks)
    with open(filename, 'wb') as f:
        for chunk in r:
            f.write(chunk)

def downloaded_strain_images():
    pass

def get_flower_df(rows):
    flower_links, flower_rows = get_flower_links(rows)

    # get strain name and if there are cannabinoid percentages
    flow_links = []
    flow_names = []
    flow_thc = []
    flow_cbd = []
    flow_active = []
    nothc = []
    nothcStrs = []
    for r in flower_rows:
        links = r.findAll('a')
        strain = links[0].text
        thc = links[1].text
        cbd = links[2].text
        activated = links[3].text
        if thc == 'N/A' or re.search('.*\%.*', thc) is None:
            nothc.append(r)
            continue

        flow_links.append(links[0].get('href'))
        flow_names.append(strain)
        flow_thc.append(thc)
        flow_cbd.append(cbd)
        flow_active.append(activated)

    flow_df = pd.DataFrame({'name':flow_names, 'link':flow_links, 'thc':flow_thc, 'cbd':flow_cbd, 'activated':flow_active})
    flow_df = flow_df.drop_duplicates()

    return flow_df

def scrape_site(df, base_im_path='analytical360/new_images/', delay=None, sql=None, mongo=None):
    '''
    goes through analytical360 site and scrapes images and data
    sql can be set to the name of a sql database to save info to, so the process can be stopped part way through
    '''
    if sql is not None:
        # didn't get this working...couldn't figure out lists in sql
        dbname=sql
        conn = psycopg2.connect("dbname=" + sql + " host='localhost'")

    if mongo is not None:
        client = MongoClient()
        db = client[mongo[0]]
        coll = db[mongo[1]]

    driver = setup_driver()
    driver.get(MAIN_URL)
    headers, cooks = get_headers_cookies(driver)
    if not os.path.exists(base_im_path):
        os.mkdir(base_im_path)
    # pages that aren't really flowers, but concentrates
    # others that have broken images links
    black_list = set(['http://analytical360.com/m/flowers/604216', 'http://analytical360.com/m/flowers/550371'])
    name_black_list = set(['Raw Pulp CJ',
                            'Batch 35 Spent Trim',
                            'B21 Spent Trim (CBD)',
                            'B21 CBD',
                            'B22 Spent Trim (THC)',
                            'ACDC x Bubster #14 Male',
                            'ACDC x Bubster #47 Male',
                            'Blue Dog #19 Male',
                            'Blue Dog #31 Male',
                            'Canna-Tsu #16 Male',
                            'Canna-Tsu #19 Male',
                            'Foo Dog #3 Male',
                            'Foo Dog #11 Male',
                            'Foo Dog #12 Male',
                            'Harle-Tsu #2 Male',
                            'Harle-Tsu #7 Male',
                            'Miami Blues #24',
                            'Swiss Gold #6 Male',
                            'Swiss Gold #18 Male',
                            'Swiss Gold #26 Male',
                            'Under Foo #8 Male',
                            'Under Foo #11 Male',
                            'Under Foo #27 Male',
                            'Under Foo #35 Male',
                            'Harle-Tsu #7Male'])

    # broke here first time thru
    # startrow = flow_df[flow_df['name'] == 'Mango Haze'].index[0]
    # df_remain = flow_df.iloc[startrow:, :]

    cannabinoids = []
    terpenes = []
    im_sources = []
    no_imgs = []
    names = []
    clean_names = []
    for i, r in df.iterrows():
        if delay is not None:
            time.sleep(delay)

        link = r['link']
        id = link.split('/')[-1]
        if link in black_list or r['name'] in name_black_list or re.search('.*male.*', r['name'], re.IGNORECASE) is not None or re.search('.*raw\s*pulp.*', r['name'], re.IGNORECASE) is not None or re.search('.*spent\s+trim.*', r['name'], re.IGNORECASE) is not None:
            continue

        clean_name = re.sub('/', '-', r['name'])
        clean_name = re.sub('[ + ' + string.punctuation + '\s]+', '', clean_name).lower()
        clean_names.append(clean_name)
        save_path = base_im_path + clean_name + id + '.jpg'
        if mongo is not None and coll.find({'link':link}).count() != 0:
            print 'already processed', r['name']
            continue

        print r['name']

        names.append(r['name'])
        driver.get(link)
        print link
        try:
            img = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[5]/div/div[1]/img[1]')
            src = img.get_attribute('src')
            im_sources.append(src)
            print src
            if os.path.exists(save_path):
                print r['name'], 'already saved image'
            else:
                print save_path
                if not isedible:
                    try:
                        download_image(src, save_path, headers, cooks)
                    except:
                        no_imgs.append(r)
                        im_sources.pop()
                        src = ''
        except:
            no_imgs.append(r)
            src = ''

        try:
            table1 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[7]/div/div[1]/ul')
        except:
            cannabinoids.append([])
            terpenes.append([])
            continue

        table1soup = bs(table1.get_attribute('innerHTML'), 'lxml')
        table1rows = [l.get_text() for l in table1soup.findAll('li')]
        isedible = False
        if re.search('serving\s*size', table1rows[0], re.IGNORECASE) is not None:
            isedible = True

        cannabinoids.append(table1rows)
        try:
            table2 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[8]/div/div/ul')
        except:
            try:
                table2 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[9]/div/div/ul')
            except:
                terpenes.append([])
                continue

        table2soup = bs(table2.get_attribute('innerHTML'), 'lxml')
        table2rows = [l.get_text() for l in table2soup.findAll('li')]
        terpenes.append(table2rows)

        coll.insert_one(
            {'cannabinoids': table1rows,
            'terpenes': table2rows,
            'clean_name': clean_name,
            'link':link,
            'im_source':src,
            'isedible':isedible,
            'save_path':save_path,
            'name': r['name']})

    client.close()

    return cannabinoids, terpenes, im_sources, no_imgs, names, clean_names

def save_raw_scrape(cannabinoids, terpenes, no_imgs, im_sources, names, clean_names, prefix=None):
    if prefix is None:
        pk.dump(cannabinoids, open('analytical360/cannabinoids.pk', 'w'), 2)
        pk.dump(terpenes, open('analytical360/terpenes.pk', 'w'), 2)
        pk.dump(no_imgs, open('analytical360/no_imgs.pk', 'w'), 2)
        pk.dump(im_sources, open('analytical360/im_sources.pk', 'w'), 2)
        pk.dump(names, open('analytical360/names.pk', 'w'), 2)
        pk.dump(clean_names, open('analytical360/clean_names.pk', 'w'), 2)
    else:
        pk.dump(cannabinoids, open('analytical360/' + prefix + 'cannabinoids.pk', 'w'), 2)
        pk.dump(terpenes, open('analytical360/' + prefix + 'terpenes.pk', 'w'), 2)
        pk.dump(no_imgs, open('analytical360/' + prefix + 'no_imgs.pk', 'w'), 2)
        pk.dump(im_sources, open('analytical360/' + prefix + 'im_sources.pk', 'w'), 2)
        pk.dump(names, open('analytical360/' + prefix + 'names.pk', 'w'), 2)
        pk.dump(clean_names, open('analytical360/' + prefix + 'clean_names.pk', 'w'), 2)

def load_raw_scrape(prefix=None):
    if prefix is None:
        cannabinoids = pk.load(open('analytical360/cannabinoids.pk'))
        terpenes = pk.load(open('analytical360/terpenes.pk'))
        no_imgs = pk.load(open('analytical360/no_imgs.pk'))
        im_sources = pk.load(open('analytical360/im_sources.pk'))
        names = pk.load(open('analytical360/names.pk'))
        clean_names = pk.load(open('analytical360/clean_names.pk'))
    else:
        cannabinoids = pk.load(open('analytical360/' + prefix + 'cannabinoids.pk'))
        terpenes = pk.load(open('analytical360/' + prefix + 'terpenes.pk'))
        no_imgs = pk.load(open('analytical360/' + prefix + 'no_imgs.pk'))
        im_sources = pk.load(open('analytical360/' + prefix + 'im_sources.pk'))
        names = pk.load(open('analytical360/' + prefix + 'names.pk'))
        clean_names = pk.load(open('analytical360/' + prefix + 'clean_names.pk'))

    return cannabinoids, terpenes, no_imgs, im_sources, names, clean_names

def parse_raw_scrape(cannabinoids, terpenes, names):
    '''
    parses raw scrape data for cannabinoids and terpenes.  Returns dataframe
    with
    '''
    trail = deque([0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1])
    cannabinoid_strs = deque(['thc-a', 'thc', 'cbn', 'thc total', 'thc-total', 'cbd-a', 'cbd', 'cbd-total', 'cbd total', 'cbg', 'cbc', 'activated total', 'activated', 'active'])
    c_dict_keys = ['thca', 'thc', 'cbn', 'thc_total', 'cbda', 'cbd', 'cbd_total', 'cbg', 'cbc', 'activated_total']
    conversion_dict = {'thc-a':'thca',
                        'thc total':'thc_total',
                        'thc-total':'thc_total',
                        'cbd-a':'cbda',
                        'cbd-total':'cbd_total',
                        'cbd total':'cbd_total',
                        'activated total':'activated_total',
                        'activated':'activated_total',
                        'active':'activated_total'} # converts similar strings to the dict key forf cannabiniod dict
    cannabinoid_dict = {}
    screen_tups = zip(range(len(trail)), trail, cannabinoid_strs)
    for i, cann in enumerate(cannabinoids):
        print i
        temp_cann = c_dict_keys[:]
        #cannabinoid_dict.setdefault('name', []).append(names[i])
        for ca in cann:
            for j, t, c in screen_tups:
                has_str, num = find_string(ca, c, t)
                if has_str:
                    # idx = list(cannabinoid_strs).index(c)
                    # cannabinoid_strs.rotate(-idx) # move that entry to the beginning of the list
                    # trail.rotate(-idx)
                    # screen_tups = zip(range(len(trail)), trail, cannabinoid_strs)
                    print 'found', c, ca
                    if c in conversion_dict:
                        cannabinoid_dict.setdefault(conversion_dict[c], []).append(num)
                        temp_cann.remove(conversion_dict[c])
                    else:
                        cannabinoid_dict.setdefault(c, []).append(num)
                        temp_cann.remove(c)
                    break

        if len(temp_cann) > 0:
            print 'didn\'t scrape:', temp_cann
            for t in temp_cann:
                cannabinoid_dict.setdefault(t, []).append('')


    terp_strs = deque(['beta-Pinene',
                        'Humulene',
                        'Limonene',
                        'alpha-Pinene',
                        'Caryophyllene',
                        'Beta Pinene',
                        'Linalool',
                        'Caryophyllene oxide',
                        'Myrcene',
                        'TERPENE-TOTAL',
                        'Terpinolene',
                        'Ocimene',
                        'Alpha Pinene'])

    t_dict_keys = ['beta_pinene',
                'alpha_pinene',
                'caryophyllene_oxide',
                'Humulene',
                'Limonene',
                'Caryophyllene',
                'Linalool',
                'Myrcene',
                'Terpinolene',
                'Ocimene',
                'total_terpenes']

    # converts similar strings to the dict key for terp dict
    terp_conv_dict = {'beta-Pinene':'beta_pinene',
                        'Beta Pinene':'beta_pinene',
                        'alpha-Pinene':'alpha_pinene',
                        'Alpha Pinene':'alpha_pinene',
                        'Caryophyllene oxide':'caryophyllene_oxide',
                        'TERPENE-TOTAL':'total_terpenes'}
    terp_dict = {}
    for i, terp in enumerate(terpenes):
        print i
        temp_cann = t_dict_keys[:]
        #terp_dict.setdefault('name', []).append(names[i])
        for ta in terp:
            for c in terp_strs:
                has_str, num = find_string(ta, c)
                if has_str:
                    idx = list(terp_strs).index(c)
                    print 'found', c, ta
                    if c in terp_conv_dict:
                        terp_dict.setdefault(terp_conv_dict[c], []).append(num)
                        temp_cann.remove(terp_conv_dict[c])
                    else:
                        terp_dict.setdefault(c, []).append(num)
                        temp_cann.remove(c)
                    break

        if len(temp_cann) > 0:
            print 'didn\'t scrape:', temp_cann
            for t in temp_cann:
                terp_dict.setdefault(t, []).append('')

    cannabinoid_dict['name'] = names
    for k in cannabinoid_dict:
        print k, len(cannabinoid_dict[k])
    for k in terp_dict:
        print k, len(terp_dict[k])

    cdf = pd.DataFrame(cannabinoid_dict)
    tdf = pd.DataFrame(terp_dict)
    total_df = cdf.merge(tdf, left_index=True, right_index=True)

    return total_df

def find_string(search_str, str_to_find='THC-A', trail=False):
    if search_str.find('8-THC') != -1:
        return 0, 0
    # if search_str.find('< 0.01 TERPENE-TOTAL') != -1:
    #     return 1, 0
    if trail:
        find_str = '.*' + str_to_find + '.*'
    else:
        find_str = '.*' + str_to_find + '$'
    has_str = 0
    res = re.search(find_str, search_str, re.IGNORECASE)
    if res:
        num = re.search('[\d\.]*', search_str).group(0)
        if search_str.find('<\s*0.01') != -1:
            return 1, 0
        return 1, num

    return 0, 0

def check_for_string(cannabinoids, str_to_find='THC-A', trail=True):
    if trail:
        find_str = '.*' + str_to_find + '.*'
    else:
        find_str = '.*' + str_to_find
    #c = [' '.join(r) for r in cannabinoids]
    has_str = []
    for c in cannabinoids:
        has_str_val = 0
        for j in c:
            res = re.search(find_str, j, re.IGNORECASE)
            if res:
                has_str_val = 1
                break

        has_str.append(has_str_val)

    return has_str

def check_if_fields_present():
    trail = [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1]
    cannabinoid_strs = ['thc-a', 'thc', 'cbn', 'thc total', 'thc-total', 'cbd-a', 'cbd', 'cbd-total', 'cbd total', 'cbg', 'cbc', 'activated total', 'activated', 'active']
    for t, c in zip(trail, cannabinoid_strs):
        has_str = check_for_string(cannabinoids, c, t)
        print c, np.mean(has_str)

def stuff():
    testdf = pd.DataFrame({'name':names})
    testdf['name'].value_counts()[testdf['name'].value_counts() > 1]


def clean_flow_df(df, clean_names=None):
    '''
    converts strings with % into floats
    '''
    new_df = df.copy()
    for c in ['activated', 'thc', 'cbd']:
        new_df[c] = new_df[c].apply(lambda x: x.strip('%'))
        new_df[c][new_df[c] == '< 0.01'] = 0
        new_df[c] = new_df[c].astype('float64')

    if clean_names is not None:
        new_df['clean_name'] = new_df['name'].apply(clean_a_name)
        new_df['im_name'] = [x['clean_name'] + x['link'].split('/')[-1] + '.jpg' for i, x in new_df.iterrows()]
        #for i, n in enumerate(clean_names):
        #     new_df.set_value(i, 'im_name', n + df.iloc[i]['link'].split('/')[-1] + '.jpg')

    return new_df

def clean_a_name(name_str):
    clean_name = re.sub('/', '-', name_str)
    clean_name = re.sub('[ + ' + string.punctuation + '\s]+', '', clean_name).lower()
    return clean_name

def match_up_leafly_names(nameset):
    ''' checks how many names roughly match in the leafly database and
    analytical360 db

    agrs: nameset -- set of names found from analytical360 to match with
    leafly strain names
    '''
    nameset = nameset.copy()
    nameset = [clean_a_name(n) for n in nameset]
    strains = sl.load_strain_list()
    strain_clean_names = [clean_a_name(n.split('/')[-1]) for n in strains]

    # to get short names:
    short_names = []
    for s in strain_clean_names:
        if len(s) < 4:
            short_names.append(s)

    skip_set = set(['ice', 'avi', 'ash', 'haze', 'thai', 'wsu', 'goo', 'or', 'ogkush', 'goat', 'flo', 'fireog', 'bsc', 'b4'])
    matches = []
    # translation from some leafly strain names to specific analytical360 names
    trans_dict = {'k1':'kk1',
                    'j1':'j1ridgewayg'}
    for s in strain_clean_names:
        # these names match too much, so we need to look for exact matches for now
        if s in skip_set:
            for f in nameset:
                if f == s:
                    matches.append((s, f))
                    break # don't need to look through the rest
                    # of the nameset if this is true
        else:
            for f in nameset:
                if f.find(s) != -1 and f.find(s + 'x') == -1:
                    matches.append((s, f))

    return matches

    # leafly_df = dp.load_data()
    # leafly_df['clean_name'] = leafly_df['product'].apply(clean_a_name)

if __name__ == "__main__":
    # attempt using selenium
    # driver = setup_driver()
    # driver.get('http://analytical360.com/testresults')
    # links = get_links_selenium(driver)

    # using requests: finding it hard to get all the correct entries
    scrape_full_site = False
    if scrape_full_site:
        res = requests.get(MAIN_URL)
        soup = bs(res.content, 'lxml')
        rows = check_rows(res)

        flow_df = get_flower_df(rows)
        flow_df.to_pickle('analytical360/flow_df.pk')
        cannabinoids, terpenes, im_sources, no_imgs, names, clean_names = scrape_site(flow_df)
        save_raw_scrape(cannabinoids, terpenes, no_imgs, im_sources, names, clean_names)
    else:
        flow_df = pd.read_pickle('analytical360/flow_df.pk')
        cannabinoids, terpenes, im_sources, no_imgs, names, clean_names = load_raw_scrape()
        clean_flow = clean_flow_df(flow_df, clean_names)

        flow_nameset = set(clean_flow['clean_name'])

        matches = match_up_leafly_names(flow_nameset)

    full_df = parse_raw_scrape(cannabinoids, terpenes, names)
    # must be some javascript to load the image...
    # requests doesn't find it
    # res1 = requests.get(flower_links[0])
    # fsoup = bs(res1.content, 'lxml')
    # ims = fsoup.findAll('img')#, {'class':'szg-main-photo szg-show'})
# for finding the images on the page with 'uploads' in the path
# uploads = []
# for i in ims:
#     try:
#         if re.search('.*uploads.*', i.get('src')):
#             uploads.append(i)
#         except:
#             continue
