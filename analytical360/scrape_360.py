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

def scrape_site():
    driver = setup_driver()
    driver.get(MAIN_URL)
    headers, cooks = get_headers_cookies(driver)
    base_im_path = 'images/'
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
    startrow = flow_df[flow_df['name'] == 'Mango Haze'].index[0]
    df_remain = flow_df.iloc[startrow:, :]

    cannabinoids = []
    terpenes = []
    im_sources = []
    no_imgs = []
    names = []
    for r in df_remain.iterrows():
        i = r[0]
        r = r[1]
        link = r['link']
        if link in black_list or r['name'] in name_black_list or re.search('.*\smale.*', r['name'], re.IGNORECASE) is not None or re.search('.*spent\s+trim.*', r['name'], re.IGNORECASE) is not None:
            continue

        names.append(r['name'])
        driver.get(link)
        print link
        try:
            img = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[5]/div/div[1]/img[1]')
            src = img.get_attribute('src')
            im_sources.append(src)
            print src
        except:
            no_imgs.append(r)

        table1 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[7]/div/div[1]/ul')
        table1soup = bs(table1.get_attribute('innerHTML'))
        table1rows = [l.get_text() for l in table1soup.findAll('li')]
        cannabinoids.append(table1rows)
        try:
            table2 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[8]/div/div/ul')
        except:
            table2 = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[9]/div/div/ul')

        table2soup = bs(table2.get_attribute('innerHTML'))
        table2rows = [l.get_text() for l in table1soup.findAll('li')]
        terpenes.append(table2rows)

        clean_name = re.sub('/', '-', r['name'])
        save_path = base_im_path + clean_name
        if os.path.exists(save_path):
            save_path = save_path + i

        save_path = save_path + '.jpg'
        print save_path

        download_image(src, save_path, headers, cooks)

def save_raw_scrape(cannabinoids, terpenes, no_imgs, im_sources, names):
    pk.dump(cannabinoids, open('analytical360/cannabinoids.pk', 'w'), 2)
    pk.dump(terpenes, open('analytical360/terpenes.pk', 'w'), 2)
    pk.dump(no_imgs, open('analytical360/no_imgs.pk', 'w'), 2)
    pk.dump(im_sources, open('analytical360/im_sources.pk', 'w'), 2)
    pk.dump(names, open('analytical360/names.pk', 'w'), 2)

def load_raw_scrape():
    cannabinoids = pk.load(open('analytical360/cannabinoids.pk'))
    terpenes = pk.load(open('analytical360/terpenes.pk'))
    no_imgs = pk.load(open('analytical360/no_imgs.pk'))
    im_sources = pk.load(open('analytical360/im_sources.pk'))
    names = pk.load(open('analytical360/names.pk'))
    return cannabinoids, terpenes, no_imgs, im_sources, names

def parse_raw_scrape(cannabinoids, terpenes, names):
    trail = [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1]
    cannabinoid_strs = ['thc-a', 'thc', 'cbn', 'thc total', 'thc-total', 'cbd-a', 'cbd', 'cbd-total', 'cbd total', 'cbg', 'cbc', 'activated total', 'activated', 'active']
    c_dict_keys = ['thca', 'thc', 'cbn', 'thc_total', 'cbda', 'cbd', 'cbd_total', 'cbg', 'cbc', 'activated_total']
    conversion_dict = {'thc-a':'thca',
                        'thc total':'thc_total',
                        'thc-total':'thc_total',
                        'cbd-a':'cbda',
                        'cbd-total':'cbd_total',
                        'cbd total':'cbd_total',
                        'activated total':'activated_total',
                        'activated':'activated_total'} # converts similar strings to the dict key forf cannabiniod dict
    cannabinoid_dict = {}
    for t, c in zip(trail, cannabinoid_strs):
        has_str, num = find_str(cannabinoids, c, t)
        if has_str:
            pass

        print c, np.mean(has_str)


    thca = []
    thc = []
    total_thc = []
    cbn = []
    cbda = []
    cbd = []
    total_cbd = []
    cbg = []
    cbc = []
    activated_total = []

def find_string(search_str, str_to_find='THC-A', trail=True):
    if trail:
        find_str = '.*' + str_to_find + '.*'
    else:
        find_str = '.*' + str_to_find
    has_str = 0
    res = re.search(find_str, j, re.IGNORECASE)
    if res:
        num = re.search('[\d\.]*').group(0)
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

if __name__ == "__main__":
    ua = UserAgent()
    # attempt using selenium
    # driver = setup_driver()
    # driver.get('http://analytical360.com/testresults')
    # links = get_links_selenium(driver)

    # using requests: finding it hard to get all the correct entries
    MAIN_URL = 'http://analytical360.com/testresults'
    res = requests.get(MAIN_URL)
    soup = bs(res.content, 'lxml')
    rows = check_rows(res)

    flow_df = get_flower_df(rows)
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
