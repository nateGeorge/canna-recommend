# drops all collections except for review_counts
from pymongo import MongoClient

DB_NAME = 'leafly'
client = MongoClient()
db = client[DB_NAME]

coll_skips = set(['system.indexes', 'review_counts'])
for c in db.collection_names():
    if c in coll_skips:
        continue
    print c
    db[c].drop()

client.close()
