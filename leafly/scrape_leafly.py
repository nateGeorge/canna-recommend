import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
import cPickle as pk

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
