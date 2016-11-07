import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pandas as pd


ua = UserAgent()


def setup_driver():
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (ua.random)
    driver = webdriver.PhantomJS(desired_capabilities=dcap)
    driver.set_window_size(1920, 1080)
    return driver


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

# attempt using selenium
# driver = setup_driver()
# driver.get('http://analytical360.com/testresults')
# links = get_links_selenium(driver)

# using requests: finding it hard to get all the correct entries
res = requests.get('http://analytical360.com/testresults')
rows = check_rows(res)
links = get_links(rows)
