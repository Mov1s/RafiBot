import MySQLdb as mdb
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read('../configs/apTrackingModule.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

#---------------------------------------------------------------
#Create the database and tables for global user tracking
#---------------------------------------------------------------

#Create database
def createDatabase():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)
		cursor = conn.cursor()
		cursor.execute('CREATE DATABASE IF NOT EXISTS rafiBot')
		conn.close()
	except:
		return False
	return True

#Create tables
def createTables():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
		cursor = conn.cursor()
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS Users
			(
				id					INT NOT NULL AUTO_INCREMENT,
				firstName			VARCHAR(1000) NOT NULL,
				lastName			VARCHAR(1000) NOT NULL,
				email				VARCHAR(1000) NOT NULL,
				mobileNumber		VARCHAR(1000) NOT NULL,
				creationDate		DATETIME NOT NULL,
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
