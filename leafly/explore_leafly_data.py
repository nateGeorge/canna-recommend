from pymongo import MongoClient
import pandas as pd
import numpy as np

DB_NAME = 'leafly_backup_2016-11-01'#'leafly'

def load_data():
    '''
    loads all review data into pandas DataFrame
    '''
    client = MongoClient()
    db = client[DB_NAME]
    total = 0
    coll_skips = set(['system.indexes', 'review_counts', 'scraped_review_pages', 'sunlight-skunk'])
    products = []
    ratings = []
    reviews = []
    dates = []
    users = []
    for c in db.collection_names():
        if c in coll_skips:
            continue

        everything = db[c].find({"scrape_times":{"$exists":False},
                               "review_count":{"$exists":False},
                               "genetics":{"$exists":False}
                               })
        for e in everything:
            products.append(c)
            ratings.append(float(e['stars']))
            reviews.append(e['text'])
            dates.append(e['date'])
            users.append(e['user'])

    df = pd.DataFrame({'rating':ratings, 'review':reviews, 'date':dates, 'user':users})
    return df
