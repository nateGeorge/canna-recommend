# drops all collections except for review_counts
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

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

def count_reviews():
    '''
    counts number of reviews for each strain in the db
    '''
    client = MongoClient()
    db = client[DB_NAME]
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c, 'number of reviews:', db[c].count()

    client.close()

def get_list_of_scraped():
    '''
    returns list of strains that have been scraped
    '''
    client = MongoClient()
    db = client[DB_NAME]
    scraped = []
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        scraped.append(c)

    client.close()
    return scraped

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

def backup_dataset():
    '''
    copies and backs up current dataset
    '''
    pass
    client = MongoClient()
    db = client[DB_NAME]
    db2 = client[DB_NAME + '_backup_' + datetime.now().isoformat()[:10]]
    for c in db.collection_names():
        if c == 'system.indexes':
            continue
        print c
        db2[c].insert_many(db[c].find())

    client.close()

def remove_dupes(test=True):
    '''
    removes dupes by matches in text entry.
    Nice example here: http://stackoverflow.com/questions/34722866/pymongo-remove-duplicates-map-reduce
    '''
    testdb_name = DB_NAME + '_backup_' + datetime.now().isoformat()[:10]
    client = MongoClient()
    if test:
        if testdb_name not in client.database_names():
            backup_dataset()
        db = client[testdb_name]
    else:
        db = client[DB_NAME]

    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
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

        print 'removing', len(response), 'dupes from', c
        db[c].delete_many({"_id": {"$in": response}})

        cursor = db[c].aggregate(
        [
            {"$group": {"_id": "$text", "unique_text": {"$addToSet": "$text"}, "count": {"$sum": 1}}},
            {"$match": {"count": { "$gte": 2 }}}
        ]
        )
        cur = list(cursor)
        if len(cur) != 0:
            raise Exception('still', len(cur), 'dupes left:', cur)

    client.close()

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
