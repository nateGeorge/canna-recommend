once you've collected data, copy a subset of it to work on before applying anything to the full dataset.  Also keep a backup of the dataset if possible.  I accidentally lost my entire scraped dataset because of a mongo command gone wrong.

careful with removing duplicates in mongo.  If an entry doesn't have the field you want to remove dupes on, anything without that field will be removed

load/dump mongodb: http://stackoverflow.com/questions/11255630/how-to-export-all-collection-in-mongodb
