import MySQLdb as mdb
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read('../configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

#---------------------------------------------------------------
#Update the AP Tracking Module database to use the user list
#Adding a row to ApRecords for the userID
#Preserves existing data by trying to migrate the current nick method to the new userId method
#---------------------------------------------------------------

#Add the new userId column to the table
def addUserIdColumn():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
		cursor = conn.cursor()
		cursor.execute('ALTER TABLE ApRecord ADD userId INT NOT NULL')
		conn.close()
	except:
		return False
	return True

#Set the userId values to the correct values based on the saved nick, do not continue until this works for everyone
def migrateNickToUserId():
	apConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	userConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
	apCursor = apConn.cursor()
	userCursor = userConn.cursor()

	apCursor.execute('SELECT nick FROM ApRecord GROUP BY nick')
	result = apCursor.fetchall()
	for row in result:
		userCursor.execute('SELECT userId FROM Nicks WHERE nick = %s', (row[0]))

		#If no user found to match the nick return an error so that migration doesn't continue
		if userCursor.rowcount == 0:
			return False

		#Change all of the apRecords to use userId		
		userResult = userCursor.fetchall()
		userId = int(userResult[0][0])
		userNick = row[0]

		apCursor.execute('UPDATE ApRecord SET userId = %s WHERE nick = %s', (userId, userNick))
		apConn.commit()

	apConn.close()
	userConn.close()

	return True	

#Remove the nick column from ApRecord
def removeNickColumn():
	try:
		conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
		cursor = conn.cursor()
		cursor.execute('ALTER TABLE ApRecord DROP nick')
		conn.close()
	except:
		return False
	return True

#Run the database scripts
def run():
	col = addUserIdColumn()
	migrate = migrateNickToUserId()
	if not col:
		print 'Error creating userId column in table'	
	if migrate:
		drop = removeNickColumn()
		if drop:
			print 'Successfully migrated database'
			return True
		else:
			print 'Error droping nicks column in table'
	elif not migrate:
		print 'Error migrating nicks to userId'
	return False

run()
