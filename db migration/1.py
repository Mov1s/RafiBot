import MySQLdb as mdb
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read('../configs/apTrackingModule.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

#---------------------------------------------------------------
#Create the database and tables for the AP Tracking Module
#---------------------------------------------------------------

#Create database
def createDatabase():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)
		cursor = conn.cursor()
		cursor.execute('CREATE DATABASE IF NOT EXISTS moduleApTracker')
		conn.close()
	except:
		return False
	return True

#Create tables
def createTables():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
		cursor = conn.cursor()
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS ApRecord
			(
				id					INT NOT NULL AUTO_INCREMENT,
				nick				VARCHAR(1000) NOT NULL,
				startTime			DATETIME NOT NULL,
				endTime				DATETIME,
				duration			INT,
				PRIMARY KEY 		(id)
			)''')
		conn.close()
	except:
		return False
	return True

#Run the database scripts
def run():
	db = createDatabase()
	tables = createTables()
	if db and tables:
		print 'Successfully migrated database'
		return True
	else:
		print 'Error migrating database'
		return False

run()
