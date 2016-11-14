import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import cPickle as pk
from datetime import datetime
import threading
import os
from glob import iglob
import multiprocessing as mp
import itertools
from pymongo import MongoClient
from fake_useragent import UserAgent
import db_functions as dbfunc
import numpy as np
import pandas as pd
import leafly.data_preprocess as dp

delay_penalty = 1  # time to wait until starting next thread if can't scrape current one
ua = UserAgent()

STRAIN_PAGE_FILE = 'leafly/leafly_alphabetic_strains_page_' + \
    datetime.utcnow().isoformat()[:10] + '.pk'
NEW_STRAIN_PAGE_FILE = 'leafly/leafly_newest_strains_page_' + \
    datetime.utcnow().isoformat()[:10] + '.pk'
BASE_URL = 'https://www.leafly.com'
STRAIN_URL = BASE_URL + '/explore/sort-alpha'

DB_NAME = 'leafly_backup_2016-11-01'  # 'leafly'


def setup_driver():
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 "
        "(KHTML, like Gecko) Chrome/15.0.87"
    )
    driver = webdriver.PhantomJS(desired_capabilities=dcap)
    driver.set_window_size(1920, 1080)
    return driver


def clear_prompts(driver):
    '''
    clears 'are you 21+?' and 'signup for newsletter' prompts
    clicks the buttons so they go away
    make sure to save and use the cookies from the driver after this
    '''
    driver.get(STRAIN_URL)
    age_screen = True
    age_count = 0
    signup = True
    signup_count = 0
    for i in range(3):
        if age_screen:
            try:
                driver.find_element_by_xpath(
                    '//a[@ng-click="answer(true)"]').click()
                print 'clicked 21+ button'
                age_screen == False
            except:
                pass

        if signup:
            try:
                driver.find_element_by_xpath(
                    '//a[@ng-click="ecm.cancel()"]').click()
                print 'clicked dont subscribe button'
                signup == False
            except:
                pass
    # for storing cookies after clicking verification buttons
    cookies = driver.get_cookies()
    cooks = {}
    for c in cookies:
        cooks[c['name']] = c['value']  # map it to be usable for requests

    return cooks


def load_current_strains(correct_names=False):
    '''
    loads most recently pickled strains list

    args: correct_names -- if True, will map weird coded names to strain names
    '''
    newest = max(iglob('strain_pages_list*.pk'), key=os.path.getctime)
    strains = pk.load(open(newest))
    if correct_names:
        product_renames = {'0bf3f759-186e-4dad-89d0-e0fc7598ac53': 'berry-white',
                           '29aca226-23ba-4726-a4ab-f3bf68f2a3c4': 'dynamite',
                           'c42aa00a-595a-4e58-a7af-0f8ab998073a': 'kaboom'}
        for i, s in enumerate(strains):
            if s.split('/')[2] in product_renames:
                temp = s.split('/')
                temp[2] = product_renames[temp[2]]
                strains[i] = '/'.join(temp)

    return strains


def load_strain_list(check=False):
    '''
    * checks for latest strain list file and loads it if it's there
    * if there, checks to make sure strain list is up to date and updates
    with new strains if necessary
    * otherwise scrolls through entire alphabetically-sorted strain list
    (takes a long time)
    '''
    driver = setup_driver()
    cooks = clear_prompts(driver)  # clears prompts and saves cookies

    newest = max(iglob('leafly/strain_pages_list*.pk'), key=os.path.getctime)
    if len(newest) > 0:
        # get list of strain pages
        strains = pk.load(open(newest))
        # check for newly-added strains
        if check:
            uptodate, diff = check_if_strains_uptodate(strains, STRAIN_URL, cooks)
            if not uptodate:
                strains = update_strainlist(diff, strains, newest)
    else:
        strain_soup = scrape_strainlist(STRAIN_PAGE_FILE, STRAIN_URL)
        strains = get_strains(strain_soup, update_pk=True)

    return strains


def update_strainlist(diff, strains, strain_file):
    '''
    checks leafly's recently added strains and adds to strain list
    '''
    strains = [s.lower() for s in strains]
    strains = sorted(list(set(strains) | diff))
    # save strainlist with todays date in filename
    strain_pages_file = 'leafly/strain_pages_list' + \
        datetime.now().isoformat()[:10] + '.pk'
    pk.dump(strains, open(strain_pages_file, 'w'), 2)

    return strains


def scrape_strainlist(save_file, strain_url=STRAIN_URL):
    '''
    scrapes leafly's strainlist (alphabetically sorted) and saves all results in
    'savefile'
    * takes a while and should only be used to initially build the strainlist
    * otherwise, use update_strainlist to get the most recent ones
    '''
    # possibility for scraping faster:
    # http://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python

    driver.get(strain_url)
    # keep clicking 'load more' until there is no more
    pause = 1
    tries = 0  # number of times tried to click button unsucessfully
    lastHeight = driver.execute_script("return document.body.scrollHeight")
    # for dealing with 21+ button and subscription button
    age_screen = True
    age_count = 0
    signup = True
    signup_count = 0
    while True:
        if age_screen:
            if age_count == 10:
                age_screen = False
            try:
                driver.find_element_by_xpath(
                    '//a[@ng-click="answer(true)"]').click()
                print 'clicked 21+ button'
                age_screen == False
            except:
                pass
            age_count += 1

        if signup:
            if signup_count == 10:
                signup = False
            try:
                driver.find_element_by_xpath(
                    '//a[@ng-click="ecm.cancel()"]').click()
                print 'clicked dont subscribe button'
                signup == False
            except:
                pass
            age_count += 1

        print 'scrolling down...'
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        try:
            driver.find_element_by_xpath(
                '//*[@id="main"]/div/section/div[2]/div/div/div[2]/div[3]/button').click()
        except Exception as e:
            print e
            tries += 1
            if tries == 3:
                break
            print 'end of strains'
        time.sleep(pause)
        newHeight = driver.execute_script("return document.body.scrollHeight")
        if newHeight == lastHeight:
            break
        lastHeight = newHeight

    res = driver.page_source
    soup = bs(res, 'lxml')
    pk.dump(res, open(save_file, 'w'), 2)
    print len(soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}))
    print len(soup.findAll('a', {'class': 'ng-scope'}))
    return soup


def check_if_strains_uptodate(strains, strain_url, cooks):
    '''
    scrapes leafly main page to check if any new strains have been added

    returns a flag (T/F) if needs update, as well as new strains/products not in
    current DB
    '''
    # need to lowercase all strains to match with updated ones
    strains = [s.lower() for s in strains]

    strain_len = len(strains) + 2  # seems to be off by 2 for some reason
    # leafly has problems counting apparantly, noticed it in the reviews
    # counts too
    print 'currently have', strain_len, 'strains'

    # get strain list sorted by newest added
    new_url = 'https://www.leafly.com/explore/sort-newest'
    res = requests.get(new_url, cookies=cooks)
    soup = bs(res.content, 'lxml')
    pk.dump(res.content, open(NEW_STRAIN_PAGE_FILE, 'w'), 2)
    new_strains = soup.findAll(
        'a', {'class': 'ga_Explore_Strain_Tile'}) + soup.findAll('a', {'class': 'ng-scope'})
    new_strains = set([s.get('href').lower() for s in new_strains])
    strain_set = set(strains)
    # check if more duplicates than just chocolate-kush (which has been
    # handled)
    coll_names = [s.split('/')[-1] for s in strain_set | new_strains]
    if len(coll_names) - len(set(coll_names)) > 1:
        df = pd.DataFrame(coll_names)
        vc = df[0].value_counts()
        print 'new duplicates:', vc[vc > 1]
        raise Exception('we got a problem: more duplicate strains')

    diff = new_strains.difference(strain_set)
    print 'missing', len(diff), 'strains in current data'
    #res = requests.get(strain_url, cookies=cooks)
    alpha_sort_soup = bs(res.content, 'lxml')
    cur_strains = int(alpha_sort_soup.findAll(
        'strong', {'ng-bind': 'totalResults'})[0].get_text())
    print 'found', cur_strains, 'strains on leafly'
    if cur_strains > strain_len or len(diff) > 0:
        print 'updating strainlist...'
        return False, diff

    print 'strainlist up-to-date!'
    return True, diff


def get_strains(strain_soup, update_pk=False, strain_pages_file=None):
    # get list of strain pages
    if strain_pages_file is None:
        strain_pages_file = 'strain_pages_list' + \
            datetime.now().isoformat()[:10] + '.pk'

    strains = strain_soup.findAll(
        'a', {'class': 'ga_Explore_Strain_Tile'}) + strain_soup.findAll('a', {'class': 'ng-scope'})
    strains = [s.get('href') for s in strains]
    if not os.path.exists(strain_pages_file) or update_pk:
        pk.dump(strains, open(strain_pages_file, 'w'), 2)

    orig = strains.copy()
    strains = set(strains)
    strains = sorted(list(strains))

    coll_names = [s.split('/')[-1] for s in orig]

    if len(coll_names) - len(set(coll_names)) > 1:
        df = pd.DataFrame(coll_names)
        vc = df[0].value_counts()
        print 'new duplicates:', vc[vc > 1]
        raise Exception('we got a problem: more duplicate strains')

    return strains


def scrape_review_page_for_num(strains, pool_size=None):
    '''
    scrape all the reviews pages and gets number of reviews for each one
    '''
    if pool_size is None:
        pool_size = mp.cpu_count()

    pool = mp.Pool(processes=pool_size)
    pool.map(func=scrape_for_num, iterable=strains)


def scrape_for_num_onedb(strain):
    '''
    scrapes leafly for number of reviews for each strain
    stores in one db called 'review_counts'
    use scrape_for_num(strain) to store in main leafly db
    '''
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }

    client = MongoClient()
    db = client[DB_NAME]
    coll = db['review_counts']

    res = requests.get(BASE_URL + strain + '/reviews',
                       headers=headers, cookies=cooks)
    soup = bs(res.content, 'lxml')
    num_reviews = int(soup.findAll(
        'span', {'class': 'hidden-xs'})[0].get_text().strip('(').strip(')'))
    print num_reviews, 'total reviews for', strain
    scrapetime = datetime.utcnow().isoformat()
    coll.insert_one(
        {'strain': strain, 'review_counts': num_reviews, 'datetime': scrapetime})
    client.close()


def scrape_for_num(strain):
    '''
    updates review_count entry for each strain based on latest from site
    '''
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }

    client = MongoClient()
    db = client[DB_NAME]
    if strain == '/Indica/chocolate-kush':
        coll = db['chocolate-kush-indica']
    else:
        coll = db[strain.split('/')[-1]]

    genetics = strain.split('/')[1]

    if coll.find({'genetics': genetics}).count() == 0:
        coll.insert_one({'genetics': genetics})
    if coll.find({'scrape_times': {'$exists': True}}).count() == 0:
        scrapetime = datetime.utcnow().isoformat()
        coll.insert_one({'scrape_times': [scrapetime]})
    if coll.find({'review_count': {'$exists': True}}).count() > 0:
        return

    rev_cnt = []
    while len(rev_cnt) == 0:
        res = requests.get(BASE_URL + strain + '/reviews',
                           headers=headers, cookies=cooks)
        soup = bs(res.content, 'lxml')
        rev_cnt = soup.findAll('span', {'class': 'hidden-xs'})
        num_reviews = int(rev_cnt[0].get_text().strip('(').strip(')'))
        time.sleep(2)

    print num_reviews, 'total reviews for', strain
    scrapetime = datetime.utcnow().isoformat()
    if coll.find({'review_count': {'$exists': True}}).count() > 0:
        coll.update_one({'review_count': {'$exists': True}}, {
                        '$push': {'review_count': num_reviews}})
    else:
        coll.insert_one({'review_count': [num_reviews]})
    client.close()

def update_reviews(strains):
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }
    # need to connect to client in each process and thread
    client = MongoClient()
    db = client[DB_NAME]

    for strain in strains:
        url = BASE_URL + s + '/reviews'
        if strain == '/Indica/chocolate-kush':
            coll = db['chocolate-kush-indica']
        else:
            coll = db[strain.split('/')[-1]]

        reviews_block = []
        while len(reviews_block) == 0:
            res = requests.get(url, cookies=cooks)
            soup = bs(res.content, 'lxml')
            reviews_block = soup.findAll('span', {'class': 'hidden-xs'})
            time.sleep(2)

        num_reviews = int(reviews_block[0].get_text().strip('(').strip(')') )
        print num_reviews, 'total reviews on site'
        cur_reviews = coll.find({'review_count':{'$exists':True}}).next()['review_count'][-1]
        if cur_reviews < num_reviews:
            genetics = strain.split('/')[1]
            num_to_scrape = num_reviews - cur_reviews
            scrape_reviews_page_threads_update(strain, url, genetics, num_to_scrape)

def scrape_reviews_page_threads_update(strain, url, genetics, num_to_scrape, verbose=True, num_threads=10):
    '''
    scrapes reviews page for all reviews
    url is a string for the specified strain homepage

    returns list of reviews
    each review consist of a tuple of (user, stars, review_text, datetime_of_review)

    num_threads is number of threads run at one time, I noticed it tends to
    not work well when more than 30 are run at once
    '''
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }
    # need to connect to client in each process and thread
    client = MongoClient()
    db = client[DB_NAME]

    if strain == '/Indica/chocolate-kush':
        coll = db['chocolate-kush-indica']
    else:
        coll = db[strain.split('/')[-1]]

    pages = num_to_scrape / 8
    scrapetime = datetime.utcnow().isoformat()
    threads = []
    if coll.find({'genetics': genetics}).count() == 0:
        coll.insert_one({'genetics': genetics})
    if coll.find({'scrape_times': {'$exists': True}}).count() == 0:
        coll.insert_one({'scrape_times': [scrapetime]})
    else:
        coll.update_one({'scrape_times': {'$exists': True}}, {
                        '$push': {'scrape_times': scrapetime}})
    if coll.find({'review_count': {'$exists': True}}).count() == 0:
        coll.insert_one({'review_count': [num_reviews]})
    else:
        coll.update_one({'review_count': {'$exists': True}}, {
                        '$push': {'review_count': num_reviews}})
        rev_cnt = coll.find({'review_count': {'$exists': True}})[0][
            'review_count'][-1] + 1  # correct for leafly miscounting
        if rev_cnt == num_reviews:
            print 'already up-to-date'
            return

    if pages < 10:
        for i in range(pages + 1):
            cur_url = url + '?page=' + str(i)
            if verbose:
                print 'scraping', cur_url
            # scrape_a_review_page(cur_url)
            t = threading.Thread(target=scrape_a_review_page, args=(cur_url,))
            t.start()
            threads.append(t)
        for th in threads:
            th.join()
    else:
        if pages > 50:
            delay = 10
        else:
            delay = 5
        for j in range(pages / 10):
            print 'scraping pages', j * 10, 'to', (j + 1) * 10
            for i in range(j * 10, (j + 1) * 10):
                cur_url = url + '?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                # scrape_a_review_page(cur_url)
                t = threading.Thread(
                    target=scrape_a_review_page, args=(cur_url,))
                t.start()
                threads.append(t)

            for th in threads:
                th.join()

            time.sleep(delay)

        if (pages % 10) != 0:
            print 'scraping pages', (j + 1) * 10, 'to', pages + 1
            for i in range((j + 1) * 10, pages + 1):
                cur_url = url + '?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                # scrape_a_review_page(cur_url)
                t = threading.Thread(
                    target=scrape_a_review_page, args=(cur_url,))
                t.start()
                threads.append(t)
            for th in threads:
                th.join()

    client.close()

def scrape_reviews_parallel(strains, pool_size=None):
    if pool_size is None:
        pool_size = mp.cpu_count()

    # mp.freeze_support()
    pool = mp.Pool(processes=pool_size)

    iterableList = []
    for i, s in enumerate(strains):
        # need to have reviews here for edibles pages
        review_page = BASE_URL + s + '/reviews'
        genetics = s.split('/')[1]
        iterableList.append([s, review_page, genetics])

    pool.map(func=scrape_reviews_page_threads_map, iterable=iterableList)


def scrape_reviews_page_threads_map(arglist):
    print 'scraping', arglist[0]  # arglist[0].split('/')[4]
    time.sleep(1.5)
    scrape_reviews_page_threads(*arglist)


def scrape_reviews_page_threads(strain, url, genetics, verbose=True, num_threads=10):
    '''
    scrapes reviews page for all reviews
    url is a string for the specified strain homepage

    returns list of reviews
    each review consist of a tuple of (user, stars, review_text, datetime_of_review)

    num_threads is number of threads run at one time, I noticed it tends to
    not work well when more than 30 are run at once
    '''
    agent = ua.random  # select a random user agent
    headers = {
        "Connection": "close",  # another way to cover tracks
        "User-Agent": agent
    }
    # need to connect to client in each process and thread
    client = MongoClient()
    db = client[DB_NAME]

    if strain == '/Indica/chocolate-kush':
        coll = db['chocolate-kush-indica']
    else:
        coll = db[strain.split('/')[-1]]

    reviews_block = []
    while len(reviews_block) == 0:
        res = requests.get(url, cookies=cooks)
        soup = bs(res.content, 'lxml')
        reviews_block = soup.findAll('span', {'class': 'hidden-xs'})
        time.sleep(2)

    num_reviews = int(reviews_block[0].get_text().strip('(').strip(')'))
    print num_reviews, 'total reviews to scrape'
    pages = num_reviews / 8
    scrapetime = datetime.utcnow().isoformat()
    threads = []
    if coll.find({'genetics': genetics}).count() == 0:
        coll.insert_one({'genetics': genetics})
    if coll.find({'scrape_times': {'$exists': True}}).count() == 0:
        coll.insert_one({'scrape_times': [scrapetime]})
    else:
        coll.update_one({'scrape_times': {'$exists': True}}, {
                        '$push': {'scrape_times': scrapetime}})
    if coll.find({'review_count': {'$exists': True}}).count() == 0:
        coll.insert_one({'review_count': [num_reviews]})
    else:
        coll.update_one({'review_count': {'$exists': True}}, {
                        '$push': {'review_count': num_reviews}})
        rev_cnt = coll.find({'review_count': {'$exists': True}})[0][
            'review_count'][-1] + 1  # correct for leafly miscounting
        if rev_cnt == num_reviews:
            print 'already up-to-date'
            return

    if num_reviews == 0:
        return

    if pages < 10:
        for i in range(pages + 1):
            cur_url = url + '?page=' + str(i)
            if verbose:
                print 'scraping', cur_url
            # scrape_a_review_page(cur_url)
            t = threading.Thread(target=scrape_a_review_page, args=(cur_url,))
            t.start()
            threads.append(t)
        for th in threads:
            th.join()
    else:
        if pages > 50:
            delay = 10
        else:
            delay = 5
        for j in range(pages / 10):
            print 'scraping pages', j * 10, 'to', (j + 1) * 10
            for i in range(j * 10, (j + 1) * 10):
                cur_url = url + '?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                # scrape_a_review_page(cur_url)
                t = threading.Thread(
                    target=scrape_a_review_page, args=(cur_url,))
                t.start()
                threads.append(t)

            for th in threads:
                th.join()

            time.sleep(delay)

        if (pages % 10) != 0:
            print 'scraping pages', (j + 1) * 10, 'to', pages + 1
            for i in range((j + 1) * 10, pages + 1):
                cur_url = url + '?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                # scrape_a_review_page(cur_url)
                t = threading.Thread(
                    target=scrape_a_review_page, args=(cur_url,))
                t.start()
                threads.append(t)
            for th in threads:
                th.join()

    client.close()


def scrape_a_review_page(url, verbose=True):
    '''
    scrapes review page and puts all the info in a mongodb, because it is unordered
    * verbose doesn't quite work correctly, lines will overlap sometimes
    '''
    global delay_penalty

    client = MongoClient()
    db = client[DB_NAME]
    strain = url.split('/')[4]
    if strain == '/Indica/chocolate-kush':
        coll = db['chocolate-kush-indica']
    else:
        coll = db[strain.split('/')[-1]]

    # for keeping track of how many pages didn't load properly
    coll2 = db['scraped_review_pages']

    res = requests.get(url, cookies=cooks)
    rev_soup = bs(res.content, 'lxml')
    reviews_soup = rev_soup.findAll(
        'li', {'class': 'page-item divider bottom padding-listItem'})
    if verbose:
        print len(reviews_soup), 'reviews on page'
    try:
        delay = 1
        if len(reviews_soup) == 0:  # try again
            for i in range(5):
                time.sleep(delay)
                delay += 1
                res = requests.get(url, cookies=cooks)
                rev_soup = bs(res.content, 'lxml')
                reviews_soup = rev_soup.findAll(
                    'li', {'class': 'page-item divider bottom padding-listItem'})
                if verbose:
                    print 'try try again:', len(reviews_soup), 'reviews on page'
                if len(reviews_soup) != 0:
                    break

        coll2.insert_one({'page': url, 'review_count': len(reviews_soup)})
        for r in reviews_soup:
            user = r.findAll('a', {'class': 'no-color'})[0].get_text()
            stars = r.findAll('span', {'class': 'squeeze'})[
                0].get('star-rating')
            text = r.findAll(
                'p', {'class': 'copy--xs copy-md--md'})[0].get_text()[1:-1]
            review_link = r.findAll(
                'a', {'class': 'copy--xs copy-md--md'})[0].get('href')
            date = r.findAll('time',
                             {'class':
                              'copy--xs copy-md--sm timestamp pull-right hidden-xs hidden-sm'}) \
                [0].get('datetime')

            datadict = {}
            datadict['user'] = user
            datadict['stars'] = stars
            datadict['text'] = text
            datadict['link'] = review_link
            datadict['date'] = date
            if coll.find(datadict).count() > 0:
                print 'already in db'
                continue
            print 'not in db, adding'
            coll.insert_one(datadict)
    except Exception as e:
        print 'ERROR DAMMIT:', e

    client.close()


def check_if_review_counts_match():
    '''
    checks if the number of reviews in the db corresponds to the number posted
    on the site.  if not, updates the reviews for that strain
    '''
    client = MongoClient()
    db = client[DB_NAME]
    coll = db['review_counts']
    all = list(coll.find())
    review_counts = {}
    for r in all:
        review_counts[r['strain'].lower()] = r['review_counts']

    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        counts = review_counts[c.lower()] + 1  # apparantly leafly can't count
        # account for scrape_time, review_counts, and genetics
        reviews = db[c].count() - 3

    client.close()


def check_if_review_counts_match_one(strain):
    '''
    checks if the number of reviews in the db corresponds to the number posted
    on the site.  This only checks the strain in the argument
    '''
    client = MongoClient()
    db = client[DB_NAME]
    coll = db['review_counts']
    try:
        entry = list(coll.find({'strain': strain}))[0]
    except Exception as e:
        print e
        return True
    review_counts = entry['review_counts'] + 1  # apparantly leafly can't count
    # account for scrape_time, review_counts, and genetics
    reviews = db[strain].count() - 3

    client.close()

    if reviews < review_counts:
        return True

    return False


def scrape_remainder(strains):
    '''
    checks the number of entries in the reviews db for each strain, and makse sure they
    add up to the expected amount.  If not, try scraping that strain again,
    and remove duplicates
    '''
    needs_update = []
    for s in strains:
        update = check_if_review_counts_match_one(s)
        if update:
            print 'needs update'
            needs_update.append(s)

    scrape_reviews_parallel(needs_update)


def get_strains_left_to_scrape(strains):
    scraped = set(dbfunc.get_list_of_scraped(DB_NAME))
    strains = np.array(strains)
    strains_abbrev = [s.split('/')[-1] for s in strains]
    mask = []
    for s in strains_abbrev:
        if s in scraped:
            mask.append(0)
        else:
            mask.append(1)

    mask = np.array(mask)
    strains_left = strains[mask == 1]
    return strains_left

def scrape_individ_pages(df):
    '''
    takes in review dataframe (i.e. from data_preprocess module)

    scrapes each individ review page for content
    places into mongo db
    '''

    client = MongoClient()
    db = client['leafly_full_reviews']
    coll = db['full_reviews']
    forms = []
    methods = []
    effects = []
    flavors = []
    locations = []
    isok = [] # for keeping track of how many requests were ok
    for i, r in df.iterrows():
        if coll.find({'link':r['link'], 'isok':True}).count() != 0:
            print 'already scraped', r['link']
            continue

        ok = False
        j = 0
        while not ok:
            j += 1
            res = requests.get(BASE_URL + r['link'])
            ok = res.ok
            if j > 0:
                time.sleep(1)
            if j == 4:
                break

        isok.append(res.ok)
        print 'on', i, 'response:', res.ok
        soup = bs(res.content, 'lxml')
        fullReview = soup.findAll('div', {'class': 'copy--md copy-md--xl padding-rowItem--xl notranslate'})[0].get_text()
        tags = soup.findAll('div', {'class':'divider bottom padding-listItem'})
        fm = tags[0].findAll('li')
        cur_form = ''
        cur_method = ''
        if len(fm) == 2:
            cur_form = fm[0].get_text().strip()
            forms.append(cur_form)
            cur_method = fm[1].get_text().strip()
            methods.append(cur_method)
        else:
            forms.append('nan')
            methods.append('nan')
        ef = tags[1].findAll('li')
        cur_effects = []
        if len(ef) > 0:
            cur_effects = [l.get_text().strip() for l in ef]

        effects.append(cur_effects)
        fl = tags[2].findAll('li')
        cur_flavors = []
        if len(fl) > 0:
            cur_flavors = [l.get_text().strip() for l in fl]

        flavors.append(cur_flavors)

        loc = soup.findAll('a', {'class':'copy--md'})
        cur_location = ''
        if len(loc) > 0:
            try:
                cur_location = loc[0].get('href')
                locations.append(cur_location)
            except:
                locations.append('')
        else:
            locations.append('')

        coll.insert_one({'link':r['link'],
                        'form':cur_form,
                        'method':cur_method,
                        'effects':cur_effects,
                        'flavors':cur_flavors,
                        'locations':cur_location,
                        'isok':res.ok,
                        'full_review':fullReview})

    client.close()

    if isok != []:
        links = df['link']
        full_df = pd.DataFrame({'link':links,
                            'form':forms,
                            'method':methods,
                            'effects':effects,
                            'flavors':flavors,
                            'locations':locations,
                            'isok':isok})

        return full_df

    return None

def scrape_individ_pages_thread(df):
    '''
    '''
    chunksize = 10

    for i in range(0, df.shape[0] + chunksize, chunksize*10):
        threads = []
        j = 0
        while j < 10:
            j += 1
            t = threading.Thread(
                target=scrape_individ_pages, args=(df.iloc[i + j*chunksize:i + (j+1)*chunksize],))
            t.start()
            threads.append(t)
            for th in threads:
                th.join()


def scrape_one_individ(r):
    '''
    takes in ONE ROW of a review dataframe (i.e. from data_preprocess module)

    scrapes each individ review page for content
    places into postgresql db
    '''

    client = MongoClient()
    db = client['leafly_full_reviews']
    coll = db['full_reviews']
    if coll.find({'link':r['link'], 'isok':True}).count() != 0:
        print 'already scraped', r['link']
        client.close()
        return None

    forms = []
    methods = []
    effects = []
    flavors = []
    locations = []

    res = requests.get(BASE_URL + r['link'])
    isok = res.ok
    print 'on', r['product'], 'response:', res.ok
    soup = bs(res.content, 'lxml')
    fullReview = soup.findAll('div', {'class': 'copy--md copy-md--xl padding-rowItem--xl notranslate'})[0].get_text()
    tags = soup.findAll('div', {'class':'divider bottom padding-listItem'})
    fm = tags[0].findAll('li')
    if len(fm) == 2:
        forms.extend(fm[0].get_text().strip().split())
        methods.extend(fm[1].get_text().strip().split())
    else:
        pass
    ef = tags[1].findAll('li')
    if len(ef) > 0:
        effects.extend([l.get_text().strip() for l in ef])
    else:
        pass
    fl = tags[2].findAll('li')
    if len(fl) > 0:
        flavors.extend([l.get_text().strip() for l in fl])
    else:
        pass

    loc = soup.findAll('a', {'class':'copy--md'})
    if len(loc) > 0:
        try:
            locations = loc[0].get('href')
        except:
            pass
    else:
        pass

    links = [r['link']]

    datadict = {'link':links,
                'form':forms,
                'method':methods,
                'effects':effects,
                'flavors':flavors,
                'locations':locations,
                'isok':isok,
                'full_review':fullReview}

    coll.insert_one({'link':r['link'],
                    'form':forms,
                    'method':methods,
                    'effects':effects,
                    'flavors':flavors,
                    'locations':locations,
                    'isok':isok,
                    'full_review':fullReview})
    client.close()

    return datadict

def scrape_individ_pages_mt(df):
    pool_size = mp.cpu_count()

    pool = mp.Pool(processes=pool_size)
    dfs = pool.map(func=scrape_one_individ, iterable=df.iterrows())

    return dfs

def finish_scraping(strains):
    '''
    finished up the initial brute-force scrape
    note some of the reviews are exact dupes
    '''
    # to re-scrape those with some missing data:
    # gonna have to run a few times...
    # this is kind of a brute-force check, which will re-srape all review pages for those strains
    ns, df = dbfunc.check_scraped_reviews()
    needs_scrape = list(df[df['needs_scrape'] == 1]['product'].values)
    needs_scrape = set([n.lower() for n in needs_scrape])
    strains_left = [s for s in strains if s.split(
        '/')[-1].lower() in needs_scrape]
    # need to update so it only scrapes until it reaches a review it already has
    scrape_reviews_parallel(strains_left)

def get_already_scraped():
    '''
    retrieves list of individual reviews already scraped
    '''
    client = MongoClient()
    db = client['leafly_full_reviews']
    coll = db['full_reviews']
    cur = coll.find({'isok':True})
    links = []
    for doc in cur:
        links.append(doc['link'])

    client.close()

    return links

if __name__ == "__main__":

    driver = setup_driver()
    cooks = clear_prompts(driver)  # clears prompts and saves cookies

    # another site to scrape:
    # base_url = 'https://weedmaps.com/'
    # url = base_url + 'dispensaries/in/united-states/colorado/denver-downtown'
    strains = load_strain_list()
    ns, df = dbfunc.check_scraped_reviews()
    strain_names = set([s.split('/')[-1].lower() for s in strains])
    scraped_strains = set([s.lower() for s in dbfunc.get_list_of_scraped()])
    # strains on the site but not in the db
    new_to_scrape = strain_names.difference(scraped_strains)
    nts = [s for s in strains if s.split(
        '/')[-1].lower() in new_to_scrape]

    scrape_new = False
    if scrape_new:
        scrape_reviews_parallel(nts)
    # strains_left = get_strains_left_to_scrape(strains)
    # chunk_size = 10 # scrape 10 strains at a time so as not to overload anything
    # while len(strains_left) > 0:
    #     print 'trying again'
    #     strains_left = get_strains_left_to_scrape(strains)
    #     scrape_reviews_parallel(strains_left)
    #     time.sleep(4)
    #finish_scraping(strains)

    #update_reviews(strains_left)

    # scrape each individ review page for effects, full review, consumption method, etc
    scrape_long = True
    if scrape_long:
        already_scraped = set(get_already_scraped())
        review_df = dp.load_data(fix_names=False, clean_reviews=False, no_anon=False, get_links=True)
        remain_df = review_df[~review_df['link'].isin(already_scraped)]
        #full_df = scrape_individ_pages(review_df) # single-throughput
        pool_size = mp.cpu_count()
        pool = mp.Pool(processes=pool_size)
        chunk_step = int(round(remain_df.shape[0] / 4.0))
        chunks = []
        for i in range(4):
            chunks.append(remain_df.iloc[i*chunk_step:(i+1)*chunk_step])
        stuff = pool.map(func=scrape_individ_pages_thread, iterable=chunks)
