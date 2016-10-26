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
    if not os.path.exists(strain_pages_file) or update:
        pk.dump(strains, open(strain_pages_file, 'w'), 2)

    return strains

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
