import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
import cPickle as pk
from datetime import datetime
import threading
import os

def scrape_strainlist(save_file):
    driver.get(strain_url)
    # keep clicking 'load more' until there is no more
    pause = 2
    tries = 0 # number of times tried to click button unsucessfully
    lastHeight = driver.execute_script("return document.body.scrollHeight")
    while True:
        print 'scrolling down...'
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            driver.find_element_by_xpath('//*[@id="main"]/div/section/div[2]/div/div/div[2]/div[3]/button').click()
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

    soup = bs(driver.page_source, 'lxml')
    pk.dump(driver.page_source, open(save_file, 'w'), 2)
    print len(soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}))
    print len(soup.findAll('a', {'class': 'ng-scope'}))
    return soup

def check_if_strains_uptodate(strains, strain_url, driver):
    '''
    scrapes leafly main page to check if any new strains have been added
    '''
    strain_len = len(strains)
    print 'currently have', strain_len, 'strains'
    driver.get(strain_url)
    alpha_sort_soup = bs(driver.page_source, 'lxml')
    cur_strains = int(alpha_sort_soup.findAll('strong', {'class':'ng-binding'})[0].get_text())
    print 'found', cur_strains, 'strains on leafly'
    if cur_strains > strain_len:
        return False
    return True

def get_strains(strain_soup, update_pk=False, strain_pages_file='strain_pages_list.pk'):
    # get list of strain pages
    strains = strain_soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}) + strain_soup.findAll('a', {'class': 'ng-scope'})
    strains = [s.get('href') for s in strains]
    if not os.path.exists(strain_pages_file) or update_pk:
        pk.dump(strains, open(strain_pages_file, 'w'), 2)

    return strains

def scrape_reviews_page_threads(driver, coll, url, genetics, verbose=True):
    '''
    scrapes reviews page for all reviews
    url is a string for the specified strain homepage

    returns list of reviews
    each review consist of a tuple of (user, stars, review_text, datetime_of_review)
    '''
    # num photos is index 1
    driver.get(url)
    soup = bs(driver.page_source, 'lxml')
    num_reviews = int(soup.findAll('span', {'class': 'hidden-xs'})[0].get_text().strip('(').strip(')'))
    print num_reviews, 'total reviews to scrape'
    pages = num_reviews / 8
    scrapetime = datetime.utcnow().isoformat()
    threads = []
    if coll.find({'genetics': genetics}).count() < 1:
        coll.insert_one({'genetics': genetics})
    if coll.find({'scrape_times': {'$exists':True}}).count() < 1:
        coll.insert_one({'scrape_times': [scrapetime]})
        coll.insert_one({'review_count': [num_reviews]})
    else:
        coll.update_one({'scrape_times': {'$exists': True}}, {'$push': {'scrape_times': scrapetime}})
        coll.update_one({'review_count': {'$exists': True}}, {'$push': {'review_count': num_reviews}})
        if coll.find({'review_count':{'$exists':'true'}}).next()['review_count'][-1] == num_reviews:
            print 'already up-to-date'
            return
    if pages < 30:
        for i in range(pages + 1):
            cur_url = url + '/reviews?page=' + str(i)
            if verbose:
                print 'scraping', cur_url
            #scrape_a_review_page(cur_url)
            t = threading.Thread(target=scrape_a_review_page, args=(coll, cur_url))
            t.start()
            threads.append(t)
        for th in threads:
            th.join()
    else:
        for j in range(pages / 30):
            print 'scraping pages', j * 30, 'to', (j + 1) * 30
            for i in range(j * 30, (j + 1) * 30):
                cur_url = url + '/reviews?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                #scrape_a_review_page(cur_url)
                t = threading.Thread(target=scrape_a_review_page, args=(coll, cur_url))
                t.start()
                threads.append(t)
            for th in threads:
                th.join()
        if (pages % 30) != 0:
            print 'scraping pages', (j + 1) * 30, 'to', pages + 1
            for i in range((j + 1) * 30, pages + 1):
                cur_url = url + '/reviews?page=' + str(i)
                if verbose:
                    print 'scraping', cur_url
                #scrape_a_review_page(cur_url)
                t = threading.Thread(target=scrape_a_review_page, args=(coll, cur_url))
                t.start()
                threads.append(t)
            for th in threads:
                th.join()

def scrape_a_review_page(coll, url, verbose=True):
    '''
    scrapes review page and puts all the info in a mongodb, because it is unordered
    '''
    res = requests.get(url)
    rev_soup = bs(res.content, 'lxml')
    reviews_soup = rev_soup.findAll('li', {'class': 'page-item divider bottom padding-listItem'})
    if verbose:
        print len(reviews_soup), 'reviews on page'
    for r in reviews_soup:
        user = r.findAll('a', {'class': 'no-color'})[0].get_text()
        stars = r.findAll('span', {'class': 'squeeze'})[0].get('star-rating')
        text = r.findAll('p', {'class': 'copy--xs copy-md--md'})[0].get_text()[1:-1]
        review_link = r.findAll('a', {'class': 'copy--xs copy-md--md'})[0].get('href')
        date = r.findAll('time', \
                         {'class': \
                          'copy--xs copy-md--sm timestamp pull-right hidden-xs hidden-sm'}) \
                            [0].get('datetime')

        datadict = {}
        datadict['user'] = user
        datadict['stars'] = stars
        datadict['text'] = text
        datadict['link'] = review_link
        datadict['date'] = date
        coll.insert_one(datadict)

if __name__ == "__main__":
    # base_url = 'https://weedmaps.com/'
    # url = base_url + 'dispensaries/in/united-states/colorado/denver-downtown'

    base_url = 'https://www.leafly.com/explore/sort-alpha'

    driver = webdriver.PhantomJS()
    driver.set_window_size(1920, 1080)
    driver.get(base_url)
    # keep clicking 'load more' until there is no more
    pause = 2
    tries = 0 # number of times tried to click button unsucessfully
    lastHeight = driver.execute_script("return document.body.scrollHeight")
    while True:
        print 'scrolling down...'
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            driver.find_element_by_xpath('//*[@id="main"]/div/section/div[2]/div/div/div[2]/div[3]/button').click()
        except exception as e:
            print exception
            tries += 1
            if tries == 3:
                break
            print 'end of strains'
        time.sleep(pause)
        newHeight = driver.execute_script("return document.body.scrollHeight")
        if newHeight == lastHeight:
            break
        lastHeight = newHeight

    soup = bs(driver.page_source, 'lxml')
    pk.dump(soup, open('leafly_strain_soup.pk', 'w'), 2)
    print len(soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}))
    print len(soup.findAll('a', {'class': 'ng-scope'}))
    # for strain in soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}):
    #     print strain.get('href')
