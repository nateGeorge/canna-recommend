import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pandas as pd
import numpy as np
import re
import os

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

driver = setup_driver()
driver.get(MAIN_URL)
headers, cooks = get_headers_cookies(driver)
base_im_path = 'images/'
if not os.path.exists(base_im_path):
    os.mkdir(base_im_path)
# pages that aren't really flowers, but concentrates
# others that have broken images links
black_list = set(['http://analytical360.com/m/flowers/604216', 'http://analytical360.com/m/flowers/550371'])
name_black_list = set(['Raw Pulp CJ', 'Batch 35 Spent Trim'])

# broke here first time thru
# startrow = flow_df[flow_df['name'] == 'Critical Cure'].index[0]
# df_remain = flow_df.iloc[:, startrow:]

cannabinoids = []
terpenes = []
im_sources = []
for r in flow_df.iterrows():
    i = r[0]
    r = r[1]
    link = r['link']
    if link in black_list or r['name'] in name_black_list:
        continue

    driver.get(link)
    print link
    try:
        img = driver.find_element_by_xpath('//*[@id="mainwrapper"]/div[4]/div[1]/div[5]/div/div[1]/img[1]')
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

    src = img.get_attribute('src')
    im_sources.append(src)
    print src
    clean_name = re.sub('/', '-', r['name'])
    save_path = base_im_path + clean_name
    if os.path.exists(save_path):
        save_path = save_path + i

    save_path = save_path + '.jpg'
    print save_path

    download_image(src, save_path, headers, cooks)

# for finding the images on the page with 'uploads' in the path
# uploads = []
# for i in ims:
#     try:
#         if re.search('.*uploads.*', i.get('src')):
#             uploads.append(i)
#         except:
#             continue
