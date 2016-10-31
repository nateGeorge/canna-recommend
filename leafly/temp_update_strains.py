# section from the update_strainlist function, just in case turns out I need it

strain_set = set(strains)
  new_url = 'https://www.leafly.com/explore/sort-newest'
  driver.get(new_url)
  # for dealing with 21+ button and subscription button
  age_screen = True
  signup = True
  for i in range(3):
      if age_screen:
          try:
              driver.find_element_by_xpath('//a[@ng-click="answer(true)"]').click()
              print 'clicked 21+ button'
              age_screen == False
          except:
              pass

      if signup:
          try:
              driver.find_element_by_xpath('//a[@ng-click="ecm.cancel()"]').click()
              print 'clicked dont subscribe button'
              signup == False
          except:
              pass

  res = driver.page_source
  soup = bs(res, 'lxml')
  new_strains = soup.findAll('a', {'class': 'ga_Explore_Strain_Tile'}) + soup.findAll('a', {'class': 'ng-scope'})
  new_strains = set([s.get('href') for s in new_strains])
