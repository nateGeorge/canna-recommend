# drops all collections except for review_counts
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

DB_NAME = 'leafly_backup_2016-11-01'  # 'leafly'


def drop_everything():
    client = MongoClient()
    db = client[DB_NAME]
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print(c)
        db[c].drop()

    client.close()


def count_reviews(dbname=DB_NAME):
    '''
    counts number of reviews for each strain in the db
    '''
    client = MongoClient()
    db = client[dbname]
    total = 0
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        count = db[c].count() - 3  # correct for info entries
        print(c, 'number of reviews:', count)
        total += count

    client.close()
    return total


def get_list_of_scraped(dbname=DB_NAME):
    '''
    returns list of strains that have been scraped
    '''
    client = MongoClient()
    db = client[dbname]
    scraped = []
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
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
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        counts += 1

    client.close()
    return counts


def backup_dataset(db1=DB_NAME, db2=None):
    '''
    copies and backs up current dataset
    '''
    if db2 is None:
        db2 = db1 + '_backup_' + datetime.now().isoformat()[:10]

    client = MongoClient()
    db_names = client.database_names()
    if db2 in db_names:
        i = 2
        while db2 in db_names:
            db2 = db2 + '_' + str(i)
            i += 1

    db = client[db1]
    db2 = client[db2]
    for c in db.collection_names():
        if c == 'system.indexes':
            continue
        print(c)
        db2[c].insert_many(db[c].find())

    client.close()


def remove_dupes(test=True, dbname=None):
    '''
    removes dupes by matches in text entry.
    Nice example here: http://stackoverflow.com/questions/34722866/pymongo-remove-duplicates-map-reduce
    '''
    client = MongoClient()
    if test:
        db_name = DB_NAME + '_backup_' + datetime.now().isoformat()[:10]
        if db_name not in client.database_names():
            backup_dataset()
        db = client[db_name]
    else:
        if dbname is None:
            db = client[DB_NAME]
        else:
            db = client[dbname]

    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        cursor = db[c].aggregate(
            [
                # sometimes have the same text but different users...e.g.
                # anonymous and not
                {"$group": {"_id": {"text": "$text", "user": "$user", "stars": "$stars", "date": "$date"},
                            "scrape_times": {"$addToSet": "$scrape_times"},
                            "review_count": {"$addToSet": "$review_count"},
                            "genetics": {"$addToSet": "$genetics"},
                            "unique_ids": {"$addToSet": "$_id"},
                            "unique_text": {"$addToSet": "$text"},
                            "count": {"$sum": 1}
                            }
                 },
                {"$match": {"count": {"$gte": 2},
                            "scrape_times": {'$exists': False},
                            "review_count": {'$exists': False},
                            "genetics": {'$exists': False}
                            }
                 }
            ]
        )

        response = []
        for doc in cursor:
            del doc["unique_ids"][0]
            for id in doc["unique_ids"]:
                response.append(id)

        print('removing', len(response), 'dupes from', c)
        db[c].delete_many({"_id": {"$in": response}})

        cursor = db[c].aggregate(
            [
                {"$group": {"_id": {"text": "$text", "user": "$user", "stars": "$stars", "date": "$date"},
                            "scrape_times": {"$addToSet": "$scrape_times"},
                            "review_count": {"$addToSet": "$review_count"},
                            "genetics": {"$addToSet": "$genetics"},
                            "unique_ids": {"$addToSet": "$_id"},
                            #"unique_text": {"$addToSet": "$text"},
                            "count": {"$sum": 1}
                            }
                 },
                {"$match": {"count": {"$gte": 2},
                            "scrape_times": {'$exists': False},
                            "review_count": {'$exists': False},
                            "genetics": {'$exists': False}
                            }
                 }
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
    coll_skips = set(['system.indexes'])
    # looks for something with a sufficient amount of entries that probably
    # has duplicates
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print(c)
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
            {"$group": {"_id": "$text", "unique_ids": {"$addToSet": "$_id"},
                        "unique_text": {"$addToSet": "$text"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 2}}}
        ]
    )

    cursor = list(cursor)
    print(cursor)
    return

    response = []
    for doc in cursor:
        del doc["unique_ids"][0]
        for id in doc["unique_ids"]:
            response.append(id)

    db[c].delete_many({"_id": {"$in": response}})

    cursor = db[c].aggregate(
        [
            {"$group": {"_id": "$text", "unique_text": {
                "$addToSet": "$text"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 2}}}
        ]
    )
    client.close()
    df = pd.DataFrame(list(db[c].find()))
    return cursor, df


def check_if_rev_count(dbname=None):
    '''
    finding that some of the entries don't have the review count
    this checks for which ones do have it, and returns a list of those that don't
    '''
    if dbname is None:
        dbname = DB_NAME

    client = MongoClient()
    db = client[dbname]
    coll_skips = set(['system.indexes', 'review_counts'])
    #
    has_rev_cnt = []
    products = []
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print(c)
        rev_cnt = db[c].find({'review_count': {'$exists': True}}).count()
        if rev_cnt > 0:
            has_rev_cnt.append(1)
        else:
            has_rev_cnt.append(0)
        products.append(c)

    df = pd.DataFrame({'product': products, 'has_review_count': has_rev_cnt})

    print('number products with review count:', df[df['has_review_count'] == 1].shape[0])
    print('number products withOUT review count:', df[df['has_review_count'] == 0].shape[0])

    return df


def check_scraped_reviews(dbname=None, rem_dupe=False):
    '''
    first removes duplicates in db
    then counts how many reviews are there for each product
    compares counts to how many were listed on the site
    returns a list of strains that need re-scraping
    '''

    # special set I noticed has count off by a bit
    blacklist = set(['cat-piss',
    'kushberry',
    'nuggetry-og',
    'master-kush',
    'somango',
    'dirty-girl',
    'cannalope-kush'])

    if dbname is None:
        dbname = DB_NAME

    client = MongoClient()
    db = client[dbname]
    if rem_dupe:
        remove_dupes(test=False, dbname=dbname)
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    #
    reviews_scraped = []
    products = []
    needs_scrape = []
    review_count = []
    for c in db.collection_names():
        if c in coll_skips:
            continue
        rev_cnt = db[c].find({'review_count': {'$exists': True}}).count()
        if rev_cnt > 0:
            rev_cnt = db[c].find({'review_count': {'$exists': True}})[
                0]['review_count'][-1]
            # sometimes review counts are off by one, other times not...
            # if rev_cnt != 0:
            #     rev_cnt += 1 # correct for leafly miscounting
            count = db[c].count() - 3  # correct for metainfo entries
            reviews_scraped.append(count)
            products.append(c)
            review_count.append(rev_cnt)
            if rev_cnt > count + 1 and c not in blacklist: # have to add one since leafly can't count...
                needs_scrape.append(1)
            else:
                needs_scrape.append(0)
        else:
            print(c)
            reviews_scraped.append(0)
            products.append(c)
            review_count.append(rev_cnt)
            needs_scrape.append(1)

    df = pd.DataFrame({'product': products, 'reviews_scraped': reviews_scraped,
                       'review_count': review_count, 'needs_scrape': needs_scrape})
    print(df[df['needs_scrape'] == 1].shape[0], 'products need scraping out of', df.shape[0])

    return needs_scrape, df


def check_for_metadata(dbname=DB_NAME):
    '''
    counts number of entries with genetics as a data field
    also for scrape_times
    '''
    client = MongoClient()
    db = client[dbname]
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    #
    products = []
    has_genetics = []
    has_time = []
    has_cnt = []
    for c in db.collection_names():
        if c in coll_skips:
            continue
        gen_cnt = db[c].find({'genetics': {'$exists': True}}).count()
        time_cnt = db[c].find({'scrape_times': {'$exists': True}}).count()
        rev_cnt = db[c].find({'review_count': {'$exists': True}}).count()
        products.append(c)
        has_genetics.append(gen_cnt)
        has_time.append(time_cnt)
        has_cnt.append(rev_cnt)

    df = pd.DataFrame({'product': products, 'gen_cnt': has_genetics,
                       'time_cnt': has_time, 'rev_cnt': has_cnt})
    print(df.shape[0], 'total products,', df.gen_cnt.sum(), \
        'count with genetics', df.time_cnt.sum(), 'with scrapetimes', \
        df.rev_cnt.sum(), 'with review_count')

    return df


def count_prods_with_no_revs(dbname=DB_NAME):
    '''
    counts number of products with no reviews, prints to console the number
    of products with and without reviews
    '''
    client = MongoClient()
    db = client[dbname]
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    #
    has_reviews = 0
    no_reviews = 0
    for c in db.collection_names():
        if c in coll_skips:
            continue
        everything = db[c].find({"scrape_times": {"$exists": False},
                                 "review_count": {"$exists": False},
                                 "genetics": {"$exists": False}
                                 })
        if len(list(everything)) != 0:
            has_reviews += 1
        else:
            no_reviews += 1

    print('number of products with reviews:', has_reviews)
    print('number of products withOUT reviews:', no_reviews)
