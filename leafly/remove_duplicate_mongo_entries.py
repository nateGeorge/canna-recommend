# since mongo 3.x it's a pain to remove dupes:
# http://stackoverflow.com/questions/14184099/fastest-way-to-remove-duplicate-documents-in-mongodb

from pymongo import MongoClient

DB_NAME = 'leafly'
client = MongoClient()
db = client[DB_NAME]
coll = db['review_counts']
serverVersion = tuple(map(int, client.server_info()['version'].split('.')))
if serverVersion[0] > 2:
    print 'can\'t remove dupes with mongo versions 3.x+'
    print 'sucks for you.  You\'ll have to consult:'
    print 'http://stackoverflow.com/questions/14184099/fastest-way-to-remove-duplicate-documents-in-mongodb'
else:
    # adapted from here: http://stackoverflow.com/questions/13190370/how-to-remove-duplicates-based-on-a-key-in-mongodb
    # but looks like a bad idea--after done once, seems to drop everything
    #coll.ensure_index('strain', unique=True, drop_dups=True)
    coll_skips = set(['system.indexes', 'review_counts'])
    for c in db.collection_names():
        if c in coll_skips:
            continue
        print c
        # whoa! this deleted everything
        # db[c].ensure_index('text', unique=True, drop_dups=True)
        # db[c].ensure_index('scrape_times', unique=True, drop_dups=True)
        # db[c].ensure_index('review_count', unique=True, drop_dups=True)
