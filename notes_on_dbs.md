currently, leafly_backup_2016-11-01 is the db with all reviews
leafly_backup_2016-11-01_leafly_backup_2016-11-01 is the backup
leafly_backup_2016-11-01_backup_2016-11-01_2 is the backup where metadata fields have been ensured to exist
to restore original:

in mongo shell:
use leafly_backup_2016-11-01
db.dropDatabase()
backup_dataset(db1='leafly_backup_2016-11-01_backup_2016-11-01_2', db2='leafly_backup_2016-11-01')


leafly only has part of the site
leafly_backup_2016-11-01_2 is the backup
