
# http://stackoverflow.com/questions/372885/how-do-i-connect-to-a-mysql-database-in-pythonimport MySQLdb
import os

PORT = 3306
DB_HOST = os.environ['CANNA_DB']
DB_UNAME = os.enviorn['CANNA_DB_UNAME']
DB_PASS = os.enviorn['CANNA_DB_PASS']
DB_NAME = 'cannadviseme'

db = MySQLdb.connect(host=DB_HOST,    # your host, usually localhost
                     user=DB_UNAME,         # your username
                     passwd=DB_PASS,  # your password
                     db=DB_NAME)        # name of the data base

cursor = db.cursor()
