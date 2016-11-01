# drops all collections except for review_counts
from pymongo import MongoClient
import pandas as pd

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

def remove_dupes():
    '''
    removes dupes by matches in all columns but _id.  Can't believe there isn't
    already a Mongo function for this already?! WTP
    '''

def subset_data():
    '''
    subsets a small amount of the main DB to play with
    '''
    client = MongoClient()
    db = client[DB_NAME]
    coll_skips = set(['system.indexes', 'review_counts'])
    # looks for something with a sufficient amount of entries that probably has duplicates
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        if db[c].count() > 99:
            break

    db2 = client['testing_leafly']
    db2[c].drop()
    entries = list(db[c].find())
    db2[c].insert_many(entries)
    client.close()
    df = pd.DataFrame(entries)
    return c, df

def test_remove_dupes(c):
    '''
    testing to make sure removing duplicates works

    args: collection name
    '''
    client = MongoClient()
    db = client['testing_leafly']
    cursor = db[c].aggregate(
    [
        {"$group": {"_id": "$text", "unique_ids": {"$addToSet": "$_id"}, "unique_text": {"$addToSet": "$text"}, "count": {"$sum": 1}}},
        {"$match": {"count": { "$gte": 2 }}}
    ]
    )

    response = []
    for doc in cursor:
        del doc["unique_ids"][0]
        for id in doc["unique_ids"]:
            response.append(id)

    db[c].delete_many({"_id": {"$in": response}})

    cursor = db[c].aggregate(
    [
        {"$group": {"_id": "$text", "unique_text": {"$addToSet": "$text"}, "count": {"$sum": 1}}},
        {"$match": {"count": { "$gte": 2 }}}
    ]
    )
    client.close()
    df = pd.DataFrame(list(db[c].find()))
    return cursor, df
