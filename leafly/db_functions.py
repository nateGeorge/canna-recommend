# drops all collections except for review_counts
from pymongo import MongoClient

DB_NAME = 'leafly'

def drop_everything():
    client = MongoClient()
    db = client[DB_NAME]
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        db[c].drop()

    client.close()

def count_strains():
    '''
    counts number of strains in db with reviews
    '''
    client = MongoClient()
    db = client[DB_NAME]
    counts = 0
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        counts += 1

    client.close()
    return counts
