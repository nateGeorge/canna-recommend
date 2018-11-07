import requests
from . import scrape_leafly as sl
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
from fake_useragent import UserAgent
import multiprocessing as mp
import os
import time
import pickle as pk

ua = UserAgent()

BASE_URL = 'https://www.leafly.com'
TEST_URL = 'https://www.leafly.com/hybrid/blue-dream'


def test_im_download():
    driver = sl.setup_driver()
    driver.get(BASE_URL)
    cooks = sl.clear_prompts(driver)

    #im = driver.find_element_by_xpath('//*[@id="main"]/div/section/div[2]/div[2]/section[5]/div[2]/img')

    # doesn't work because s3 bucket is private

    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }

    res = requests.get(TEST_URL, headers=headers, cookies=cooks)
    soup = bs(res.content)
    ims = soup.findAll('img', {'class': 'l-img-responsive'})
    imurl = None
    for i in ims:
        src = i.get('src')
        print(src)
        if re.search('.*strains/testing.*', src) is not None:
            imurl = src

    if imurl is not None:
        # fetch image and save it
        r = requests.get(imurl, headers=headers, cookies=cooks)
        with open('test.png', 'wb') as f:
            for chunk in r:
                f.write(chunk)


def get_chem_images(strains):
    '''
    scrapes all chemistry info images from strain pages, if they have one
    '''
    driver = sl.setup_driver()
    driver.get(BASE_URL)
    cooks = sl.clear_prompts(driver)
    all_imurls = []
    for s in strains:
        if s.split('/')[1].lower() == 'edible':
            continue
        print('checking', s)
        agent = ua.random  # select a random user agent
        headers = {
            "Connection": "close",  # another way to cover tracks
            "User-Agent": agent
        }

        res = requests.get(BASE_URL + s, headers=headers, cookies=cooks)
        soup = bs(res.content)
        ims = soup.findAll('img', {'class': 'l-img-responsive'})
        imurl = None
        for i in ims:
            src = i.get('src')
            if re.search('.*strains/testing.*', src) is not None:
                imurl = src

        if imurl is not None:
            print('found imurl:', imurl)
            all_imurls.append(imurl)

    return all_imurls


def get_one_chem_im(strain_cooks_tuple):
    '''
    checks one strain page for a strain fingerprint image
    '''
    s = strain_cooks_tuple[0]
    cooks = strain_cooks_tuple[1]
    if s.split('/')[1].lower() == 'edible':
        return
    print('checking', s)
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }

    res = requests.get(BASE_URL + s, headers=headers, cookies=cooks)
    if not res.ok:
        for i in range(3):
            time.sleep(0.5)
            res = requests.get(BASE_URL + s, headers=headers, cookies=cooks)
            if res.ok:
                break

    soup = bs(res.content)
    ims = soup.findAll('img', {'class': 'l-img-responsive'})
    imurl = None
    for i in ims:
        src = i.get('src')
        if re.search('.*strains/testing.*', src) is not None:
            imurl = src
            print('found', imurl)

    return s, imurl, res


def multithread_dl_ims(strains, cooks):
    '''
    gets images links for each strain page with multithreading
    takes list of strain pages (i.e. /hybrid/blue-dream)
    and cookies from selenium driver as dict (cooks)
    '''
    pool_size = mp.cpu_count()
    pool = mp.Pool(processes=pool_size)
    a = pool.map(func=get_one_chem_im, iterable=list(zip(
        strains, [cooks] * len(strains))))
    return [i for i in a if i is not None]


def setup_driver():
    driver = sl.setup_driver()
    driver.get(BASE_URL)
    cooks = sl.clear_prompts(driver)
    return driver, cooks


def save_imdict(im_dict):
    '''
    saves dict of strains and links to strain fingerprint image
    '''
    pk.dump(im_dict, open('im_dict.pk', 'w'), 2)


def download_images(im_dict):
    '''
    downloads all the images from the im_dict
    '''
    global cooks
    main_dir = 'strain_fingerprints/'
    if not os.path.exists(main_dir):
        os.mkdir(main_dir)

    for s in im_dict:
        agent = ua.random  # select a random user agent
        headers = {
            "Connection": "close",  # another way to cover tracks
            "User-Agent": agent
        }
        r = requests.get(im_dict[s], headers=headers, cookies=cooks)
        with open(main_dir + re.sub('/', '_', s) + '.png', 'wb') as f:
            for chunk in r:
                f.write(chunk)


def make_im_res_dicts(scraped_urls):
    '''
    takes list of tuples from multiprocessing and breaks into dicts
    '''
    im_dict = {}
    res_dict = {}  # for keeping track of which requests failed
    for i in scraped_urls:
        strain = i[0]
        imurl = i[1]
        res = i[2]
        if imurl is not None:
            im_dict[strain] = imurl
        res_dict[strain] = res

    return im_dict, res_dict


def check_how_many_ok(res_dict):
    '''
    checks how many requests were ok (status 200 or similar)
    '''
    ok_dict = {}
    not_ok_dict = {}
    for s in res_dict:
        if res_dict[s].ok:
            ok_dict[s] = 1
        else:
            not_ok_dict[s] = 1

    return ok_dict, not_ok_dict


driver, cooks = setup_driver()
strains = sl.load_current_strains()
scraped_urls = multithread_dl_ims(strains, cooks)
im_dict, res_dict = make_im_res_dicts(scraped_urls)
ok_dict, not_ok_dict = check_how_many_ok(res_dict)
