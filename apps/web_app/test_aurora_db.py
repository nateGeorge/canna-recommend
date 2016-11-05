# install mysqldb on ubuntu: https://edwards.sdsu.edu/research/installing-mysqldb-module-for-python-2-7-for-ubuntu-12-04/
# http://stackoverflow.com/questions/372885/how-do-i-connect-to-a-mysql-database-in-pythonimport MySQLdb
import MySQLdb
import os

PORT = 3306
DB_HOST = os.environ['CANNA_DB']
DB_UNAME = os.environ['CANNA_DB_UNAME']
DB_PASS = os.environ['CANNA_DB_PASS']
DB_NAME = os.environ['CANNA_DB_NAME']

db = MySQLdb.connect(host=DB_HOST,    # your host, usually localhost
                     user=DB_UNAME,         # your username
                     passwd=DB_PASS,  # your password
                     db=DB_NAME)        # name of the data base

cursor = db.cursor()

cursor.execute('CREATE TABLE test (id INT, date DATETIME);')

cursor.execute('SHOW TABLES;')

res = cursor.fetchall()

print res[0][0]
