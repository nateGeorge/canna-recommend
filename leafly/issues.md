D1:
Scraping coding is becoming huge, and having some problems in the threads.  For example:
sometimes 0 results are returned (i.e. the page doesn't load).  Sometimes after a few tries it reloads.  Ideas for error handling?
Same thing with the first page that checks number of reviews.  

Removing dupes in mongo sucks.


D2:
Scraping function wasn't storing everything in the db I thought it should've been, had to write another function to re-grab what it wasn't getting.  Found a strain with the same name (chocolate kush) in both the hybrid and indica sections, which was screwing up the db since the collections are named by the product name

Another problem was the removing duplicates function.  When aggregating in mongo, if the entry doesn't have the field you're trying to aggregate on, you have to make an exception for that, and ignore it in the match part of the aggregation.

Review counts are not correct: for example,
https://www.leafly.com/hybrid/hobbit/reviews?page=0
says 1 review, but there are none.


D5:
Figured out my drop_duplicates mongo function wasn't working.  Think it had something to do with the 
Need to clean data more.  For some reason, death-star has way more reviews than it should.  Also, there are duplicate reviews that need to be cleaned, e.g.:

40242  Really nice strain, first time i have tried th...      stonedfoxx23   
40243  Really nice strain, first time i have tried th...         Anonymous

in death-star
