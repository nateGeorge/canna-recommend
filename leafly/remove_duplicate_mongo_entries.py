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
else:
    coll.ensure_index('strain', unique=True, drop_dups=True)
