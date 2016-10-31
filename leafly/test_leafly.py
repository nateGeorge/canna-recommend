import unittest
import scrape_leafly as sl
import selenium

class TestScraping(unittest.TestCase):

    def test_upper(self):
        soup = sl.scrape_strainlist()
        strains = soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'})
        self.assertEqual(type(strains), list)

    def test_driver_creation(self):
        driver = sl.create_driver()
        self.asssertEqual(type(driver), selenium.webdriver.phantomjs.webdriver.WebDriver)

if __name__ == '__main__':
    unittest.main()
