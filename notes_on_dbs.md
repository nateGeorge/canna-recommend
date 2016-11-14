currently, leafly_backup_2016-11-01 is the db with all reviews
leafly_backup_2016-11-01_leafly_backup_2016-11-01 is the backup
leafly_backup_2016-11-01_backup_2016-11-01_2 is the backup where metadata fields have been ensured to exist
leafly_backup_2016-11-01_backup_2016-11-13 is the latest, with metadata and all reviews up to that date

to restore original:

in mongo shell:
use leafly_backup_2016-11-01
db.dropDatabase()
# hmm doesn't seem to work...
backup_dataset(db1='leafly_backup_2016-11-01_backup_2016-11-01_2', db2='leafly_backup_2016-11-01')

# this works, however
db.copyDatabase(fromdb='leafly_backup_2016-11-01_backup_2016-11-01_2_3', todb='leafly_backup_2016-11-01')


leafly only has part of the site
leafly_backup_2016-11-01_2 is the backup


# to get most recent entry in a mongodb:
db['full_reviews'].find().sort({$natural:-1}).limit(1)
